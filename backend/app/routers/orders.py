from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
import uuid

from ..database import get_db
from ..models import Product, Order, OrderItem, OrderStatusEnum, UserRole, PromoCode, DeliveryMethod
from ..models.models import generate_order_number, generate_or_number
from ..services import StockReservationService, ReceiptPDFService
from ..auth.dependencies import get_current_salesman_or_admin, CurrentUser
from ..schemas import OrderResponse, OrderItemResponse, OrderCreate, DeliveryMethod as DeliveryMethodSchema

router = APIRouter(prefix="/orders", tags=["orders"])


def build_order_response(order: Order) -> dict:
    """Build order response with items and product details."""
    items = []
    if order.items:
        for item in order.items:
            items.append(OrderItemResponse(
                product_id=item.product_id,
                product_name=item.product.name if item.product else "Unknown",
                product_sku=item.product.sku if item.product else None,
                product_image_url=item.product.image_url if item.product else None,
                quantity=item.quantity,
                unit_price=float(item.unit_price)
            ).model_dump())

    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        or_number=order.or_number,
        customer_name=order.customer_name,
        delivery_method=order.delivery_method,
        address=order.address,
        total_price=float(order.total_price),
        discount_amount=float(order.discount_amount) if order.discount_amount else 0.0,
        applied_promo_id=order.applied_promo_id,
        status=order.status,
        remark=order.remark,
        user_id=order.user_id,
        created_at=order.created_at,
        items=items
    ).model_dump()


async def validate_promo_code(db: AsyncSession, code: str) -> dict:
    """Validate a promo code and return discount info."""
    result = await db.execute(
        select(PromoCode).filter(PromoCode.code == code)
    )
    promo = result.scalar_one_or_none()

    if not promo:
        return {"valid": False, "message": "Invalid promo code"}

    if not promo.is_active:
        return {"valid": False, "message": "Promo code is no longer active"}

    if promo.expiry_date and promo.expiry_date < datetime.now(timezone.utc):
        return {"valid": False, "message": "Promo code has expired"}

    return {
        "valid": True,
        "code": promo.code,
        "discount_type": promo.discount_type,
        "discount_value": promo.value,
        "message": "Promo code applied successfully"
    }


async def apply_discount(total_price: float, discount_type: str, discount_value: float) -> float:
    """Calculate discount amount based on type."""
    if discount_type == "percentage":
        return round(total_price * (discount_value / 100), 2)
    elif discount_type == "flat":
        return min(discount_value, total_price)
    return 0.0


@router.get("/")
async def list_orders(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_salesman_or_admin)
):
    """List orders with role-based data isolation.

    - Salesmen see ONLY their own orders (filtered by user_id)
    - Admins see ALL orders in the system
    """
    query = select(Order).options(
        selectinload(Order.items).joinedload(OrderItem.product)
    )

    # Role-Based Data Isolation: Salesmen only see their own orders
    if current_user.role == UserRole.SALESMAN.value:
        query = query.filter(Order.user_id == current_user.id)

    result = await db.execute(query.order_by(Order.created_at.desc()))
    orders = result.scalars().unique().all()

    return [build_order_response(o) for o in orders]


@router.get("/{order_id}")
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_salesman_or_admin)
):
    """Get a single order with ownership check.

    - Salesmen can ONLY view their own orders
    - Admins can view ALL orders
    """
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items).joinedload(OrderItem.product))
        .filter(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Role-Based Data Isolation: Salesmen cannot access other users' orders
    if not current_user.can_access_order(order.user_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied: you can only view your own orders"
        )

    return build_order_response(order)


@router.post("/", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_salesman_or_admin)
):
    """Create a new order with atomic stock reservation.

    Both Salesman and Admin roles can create orders.
    The order is tagged with the creating user's ID for data isolation.

    - customer_name is required
    - address is mandatory ONLY if delivery_method is 'Delivery'
    - promo_code is optional (single code only - multiple codes will be rejected)
    - Uses SELECT FOR UPDATE for row-level locking to prevent overselling
    - Auto-generates unique or_number (Official Receipt)
    """
    # Validate customer_name is provided
    if not order_data.customer_name or not order_data.customer_name.strip():
        raise HTTPException(status_code=400, detail="Customer name is required")

    # Validate address for delivery orders
    if order_data.delivery_method == DeliveryMethod.DELIVERY:
        if not order_data.address or not order_data.address.strip():
            raise HTTPException(status_code=400, detail="Address is required for delivery orders")

    if not order_data.items:
        raise HTTPException(status_code=400, detail="Order must have at least one item")

    # SINGLE PROMO CODE RESTRICTION - Only one promo code allowed per order
    # Reject if promo_code is a list (stacking attempt via payload manipulation)
    promo_code_value: str | None = None
    if order_data.promo_code is not None:
        promo_val = order_data.promo_code
        if isinstance(promo_val, list):
            raise HTTPException(status_code=400, detail="Only one promo code allowed per order")
        if isinstance(promo_val, str) and "," in promo_val:
            raise HTTPException(status_code=400, detail="Only one promo code allowed per order")
        promo_code_value = promo_val  # type: ignore[assignment]

    # Start atomic transaction
    try:
        # Collect product info and validate stock with row-level locking
        order_items_data = []
        total_price = 0.0
        locked_product_ids = set()

        for item in order_data.items:
            # Lock the product row with SELECT FOR UPDATE (PostgreSQL/MySQL)
            # SQLite does not support FOR UPDATE, so we use a regular SELECT
            try:
                result = await db.execute(
                    text("""
                        SELECT id, sku, name, price, physical_stock, reserved_stock, image_url
                        FROM products
                        WHERE id = :product_id
                        FOR UPDATE
                    """),
                    {"product_id": item.product_id}
                )
            except Exception:
                # Fallback for SQLite and other databases that don't support FOR UPDATE
                result = await db.execute(
                    text("""
                        SELECT id, sku, name, price, physical_stock, reserved_stock, image_url
                        FROM products
                        WHERE id = :product_id
                    """),
                    {"product_id": item.product_id}
                )
            product_row = result.fetchone()

            if not product_row:
                raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")

            product_id, sku, name, price, physical_stock, reserved_stock, image_url = product_row
            available_stock = physical_stock - reserved_stock

            # Verify sufficient stock
            if available_stock < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for product '{name}' (SKU: {sku}). "
                           f"Available: {available_stock}, Requested: {item.quantity}"
                )

            # Calculate item price
            item_price = price * item.quantity
            total_price += item_price

            order_items_data.append({
                "product_id": product_id,
                "product_name": name,
                "product_image_url": image_url,
                "quantity": item.quantity,
                "unit_price": price
            })

        # Apply promo code discount if provided
        discount_amount = 0.0
        applied_promo_id = None
        if promo_code_value:
            promo_validation = await validate_promo_code(db, promo_code_value)
            if not promo_validation["valid"]:
                raise HTTPException(status_code=400, detail=promo_validation["message"])

            # Get the promo record to save its ID
            promo_result = await db.execute(
                select(PromoCode).filter(PromoCode.code == promo_code_value.upper())
            )
            promo_record = promo_result.scalar_one_or_none()
            if promo_record:
                applied_promo_id = promo_record.id

            discount_amount = await apply_discount(
                total_price,
                promo_validation["discount_type"],
                promo_validation["discount_value"]
            )

        # Calculate final total
        final_total = round(total_price - discount_amount, 2)

        # Generate order number and OR number
        order_number = generate_order_number()
        or_number = generate_or_number()

        # Create the order
        order = Order(
            order_number=order_number,
            or_number=or_number,
            customer_name=order_data.customer_name.strip(),
            delivery_method=order_data.delivery_method.value,
            address=order_data.address.strip() if order_data.address else None,
            total_price=final_total,
            discount_amount=discount_amount,
            status=OrderStatusEnum.PENDING_PAYMENT.value,
            remark=order_data.remark.strip() if order_data.remark else None,
            user_id=current_user.id,
            applied_promo_id=applied_promo_id
        )
        db.add(order)
        await db.flush()

        # Create order items and deduct stock atomically
        for item_data in order_items_data:
            # Create order item
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data["product_id"],
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"]
            )
            db.add(order_item)

            # Deduct physical stock immediately (atomic with order creation)
            result = await db.execute(
                text("""
                    UPDATE products
                    SET physical_stock = physical_stock - :qty,
                        version = version + 1
                    WHERE id = :product_id
                    AND physical_stock >= :qty
                """),
                {"product_id": item_data["product_id"], "qty": item_data["quantity"]}
            )

            if result.rowcount == 0:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to deduct stock for product {item_data['product_id']}"
                )

        # Commit the transaction
        await db.commit()

        # Refetch order with items and products for response
        result = await db.execute(
            select(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .filter(Order.id == order.id)
        )
        order_with_items = result.scalar_one()

        return build_order_response(order_with_items)

    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")


@router.post("/{order_id}/request-cancel")
async def request_cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_salesman_or_admin)
):
    """Request order cancellation.

    - Salesmen can ONLY cancel their own orders
    - Admins cannot use this endpoint (use admin force-cancel instead)
    """
    result = await db.execute(select(Order).filter(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Role-Based Data Isolation: Salesmen can only cancel their own orders
    if not current_user.can_access_order(order.user_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied: you can only cancel your own orders"
        )

    if order.status not in [
        OrderStatusEnum.PENDING_PAYMENT.value,
        OrderStatusEnum.PAYMENT_UNDER_REVIEW.value
    ]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order with status '{order.status}'"
        )

    order.status = OrderStatusEnum.CANCEL_REQUESTED.value
    await db.commit()

    return {
        "order_id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "message": "Cancel request submitted. Waiting for admin approval."
    }


@router.post("/{order_id}/upload-payment")
async def upload_payment(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_salesman_or_admin)
):
    """Upload payment receipt for an order.

    - Salesmen can ONLY upload payments for their own orders
    - Admins can upload payments for ALL orders
    """
    result = await db.execute(select(Order).filter(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Role-Based Data Isolation: Salesmen can only upload to their own orders
    if not current_user.can_access_order(order.user_id):
        raise HTTPException(status_code=403, detail="Access denied: you can only upload payments for your own orders")

    if order.status != OrderStatusEnum.PENDING_PAYMENT.value:
        raise HTTPException(status_code=400, detail=f"Order is not pending payment. Status: {order.status}")

    from ..models import Payment
    payment = Payment(
        order_id=order_id,
        receipt_url=f"/uploads/{order_id}/receipt",
        uploaded_at=datetime.utcnow()
    )
    db.add(payment)
    order.status = OrderStatusEnum.PAYMENT_UNDER_REVIEW.value

    await db.commit()

    return {
        "id": payment.id,
        "order_id": payment.order_id,
        "receipt_url": payment.receipt_url,
        "uploaded_at": payment.uploaded_at.isoformat() if payment.uploaded_at else None
    }


@router.get("/{order_id}/receipt")
async def get_order_receipt(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_salesman_or_admin)
):
    """Generate and download the Official Receipt PDF for an order.

    - Salesmen can ONLY download receipts for their own orders
    - Admins can download receipts for ALL orders

    Returns a PDF file that can be viewed in the browser or downloaded.
    """
    # Fetch order with items
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Role-Based Data Isolation: Salesmen can only access their own receipts
    if not current_user.can_access_order(order.user_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied: you can only view receipts for your own orders"
        )

    # Build items list for the PDF
    items_data = []
    subtotal = 0.0

    for item in order.items:
        item_data = {
            "product_name": item.product.name if item.product else "Unknown Product",
            "quantity": item.quantity,
            "unit_price": float(item.unit_price)
        }
        items_data.append(item_data)
        subtotal += item.quantity * item.unit_price

    # Generate PDF
    pdf_buffer = ReceiptPDFService.generate_receipt_pdf(
        or_number=order.or_number,
        order_number=order.order_number,
        timestamp=order.created_at or datetime.utcnow(),
        customer_name=order.customer_name,
        delivery_method=order.delivery_method,
        address=order.address,
        items=items_data,
        subtotal=subtotal,
        discount_amount=float(order.discount_amount) if order.discount_amount else 0.0,
        total_price=float(order.total_price)
    )

    # Generate filename
    filename = f"OR_{order.or_number.replace('-', '_')}.pdf"

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename={filename}",
            "Content-Transfer-Encoding": "binary",
        }
    )
