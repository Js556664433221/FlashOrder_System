from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime
import uuid
import logging
import hashlib

logger = logging.getLogger(__name__)

from ..database import get_db
from ..models import Product, Order, OrderItem, Payment, OrderStatusEnum, User, PromoCode, DeliveryMethod, ActivityAction
from ..schemas import (
    AdminProductCreate, AdminProductUpdate, AdminProductResponse,
    AdminOrderUpdate, AdminOrderResponse, AdminPaymentResponse,
    AdminOrderStatus, AdminPaymentStatus, OrderItemWithProduct,
    VerifyPaymentRequest, VerifyPaymentResponse,
    RejectPaymentRequest,
    RestockRequest, RestockResponse, DashboardSummaryResponse, LowStockProduct,
    ForceCancelResponse, UserResponse, UserStatusUpdateResponse, UserStatus,
    CreateAdminRequest, CreateAdminResponse, PromoteUserResponse
)
from ..services import StockReservationService, ActivityLogService
from ..auth.dependencies import get_current_admin, CurrentUser

router = APIRouter(prefix="/admin", tags=["admin"])


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


async def require_initial_admin(
    current_user: CurrentUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Verify that the current user is a Super Admin (is_superadmin=True).

    Only Super Admins can:
    - Create new admin users
    - Promote users to admin role

    Args:
        current_user: User from get_current_admin dependency
        db: Database session

    Returns:
        User if user is a Super Admin

    Raises:
        HTTPException: If user is not a Super Admin
    """
    # Fetch the user from database to check is_superadmin flag
    result = await db.execute(select(User).filter(User.id == current_user.id))
    user = result.scalar_one_or_none()

    if not user or user.is_superadmin != 1:
        raise HTTPException(
            status_code=403,
            detail="Only the Super Admin can perform this action"
        )

    return user

LOW_STOCK_THRESHOLD = 10


def get_stock_status(order_status: str) -> str:
    """Determine stock status based on order status."""
    if order_status in (
        OrderStatusEnum.PENDING_PAYMENT.value,
        OrderStatusEnum.PAYMENT_UNDER_REVIEW.value,
        OrderStatusEnum.PAYMENT_REJECTED.value,
        "Pending Payment",
        "Payment Under Review",
        "Payment Rejected",
    ):
        return "Reserved"
    elif order_status in (
        OrderStatusEnum.PAID.value,
        OrderStatusEnum.PREPARING.value,
        OrderStatusEnum.READY_FOR_PICKUP.value,
        OrderStatusEnum.SHIPPED.value,
        OrderStatusEnum.COMPLETED.value,
        "Paid",
        "Preparing",
        "Ready for Pickup",
        "Shipped",
        "Completed",
    ):
        return "Deducted"
    elif order_status in (
        OrderStatusEnum.CANCELLED.value,
        OrderStatusEnum.CANCEL_REQUESTED.value,
        "Cancelled",
    ):
        return "Released"
    return "Unknown"


def generate_sku() -> str:
    """Generate a unique SKU."""
    return f"SKU-{uuid.uuid4().hex[:8].upper()}"


def build_admin_order_response(order: Order) -> AdminOrderResponse:
    """Helper to build AdminOrderResponse from an Order."""
    items_with_product = [
        OrderItemWithProduct(
            id=item.id,
            order_id=item.order_id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            product_name=item.product.name if item.product else "Unknown",
            product=AdminProductResponse(
                id=item.product.id,
                sku=item.product.sku,
                name=item.product.name,
                description=item.product.description,
                image_url=item.product.image_url,
                physical_stock=item.product.physical_stock,
                reserved_stock=item.product.reserved_stock,
                available_stock=item.product.physical_stock - item.product.reserved_stock,
                price=float(item.product.price),
                version=item.product.version
            ),
            stock_status=get_stock_status(order.status)
        )
        for item in order.items
    ]

    payment_data = None
    if order.payments:
        latest_payment = max(order.payments, key=lambda p: p.uploaded_at)
        payment_data = AdminPaymentResponse(
            id=latest_payment.id,
            order_id=latest_payment.order_id,
            receipt_url=latest_payment.receipt_url,
            rejection_reason=latest_payment.rejection_reason,
            rejected_at=latest_payment.rejected_at,
            uploaded_at=latest_payment.uploaded_at
        )

    return AdminOrderResponse(
        id=order.id,
        order_number=order.order_number,
        total_price=order.total_price,
        status=order.status,
        remark=order.remark,
        created_at=order.created_at,
        items=items_with_product,
        payment=payment_data
    )


def build_product_response(product: Product) -> AdminProductResponse:
    """Build product response with stock details."""
    return AdminProductResponse(
        id=product.id,
        sku=product.sku,
        name=product.name,
        description=product.description,
        image_url=product.image_url,
        physical_stock=product.physical_stock,
        reserved_stock=product.reserved_stock,
        available_stock=product.physical_stock - product.reserved_stock,
        price=float(product.price),
        version=product.version
    )


def validate_status_transition(current_status: str, new_status: str) -> bool:
    """Validate if status transition is allowed."""
    valid_transitions = {
        OrderStatusEnum.PENDING_PAYMENT.value: [
            OrderStatusEnum.PAYMENT_UNDER_REVIEW.value,
            OrderStatusEnum.CANCEL_REQUESTED.value,
            OrderStatusEnum.CANCELLED.value,
        ],
        OrderStatusEnum.PAYMENT_UNDER_REVIEW.value: [
            OrderStatusEnum.PAID.value,
            OrderStatusEnum.PAYMENT_REJECTED.value,
            OrderStatusEnum.CANCEL_REQUESTED.value,
            OrderStatusEnum.CANCELLED.value,
        ],
        OrderStatusEnum.PAYMENT_REJECTED.value: [
            OrderStatusEnum.PAYMENT_UNDER_REVIEW.value,  # Can re-upload
            OrderStatusEnum.CANCEL_REQUESTED.value,
            OrderStatusEnum.CANCELLED.value,
        ],
        OrderStatusEnum.PAID.value: [
            OrderStatusEnum.PREPARING.value,
            OrderStatusEnum.READY_TO_SHIP.value,
            OrderStatusEnum.READY_FOR_PICKUP.value,
            OrderStatusEnum.SHIPPED.value,
            OrderStatusEnum.COMPLETED.value,
            OrderStatusEnum.CANCELLED.value,
        ],
        OrderStatusEnum.PREPARING.value: [
            OrderStatusEnum.READY_TO_SHIP.value,
            OrderStatusEnum.READY_FOR_PICKUP.value,
            OrderStatusEnum.READY_FOR_COLLECTION.value,
            OrderStatusEnum.SHIPPED.value,
            OrderStatusEnum.COMPLETED.value,
            OrderStatusEnum.CANCELLED.value,
        ],
        OrderStatusEnum.READY_TO_SHIP.value: [
            OrderStatusEnum.SHIPPED.value,
            OrderStatusEnum.COMPLETED.value,
            OrderStatusEnum.CANCELLED.value,
        ],
        OrderStatusEnum.READY_FOR_PICKUP.value: [
            OrderStatusEnum.SHIPPED.value,
            OrderStatusEnum.COMPLETED.value,
            OrderStatusEnum.CANCELLED.value,
        ],
        OrderStatusEnum.READY_FOR_COLLECTION.value: [
            OrderStatusEnum.COMPLETED.value,
            OrderStatusEnum.CANCELLED.value,
        ],
        OrderStatusEnum.SHIPPED.value: [
            OrderStatusEnum.COMPLETED.value,
        ],
        OrderStatusEnum.COMPLETED.value: [],
        OrderStatusEnum.CANCEL_REQUESTED.value: [
            OrderStatusEnum.CANCELLED.value,
            OrderStatusEnum.PAID.value,
        ],
        OrderStatusEnum.CANCELLED.value: [],
        # Legacy string values for compatibility
        "Paid": ["Preparing", "Ready to Ship", "Ready for Pickup", "Shipped", "Completed", "Cancelled"],
        "Preparing": ["Ready to Ship", "Ready for Pickup", "Ready for Collection", "Shipped", "Completed", "Cancelled"],
        "Ready to Ship": ["Shipped", "Completed", "Cancelled"],
        "Ready for Pickup": ["Shipped", "Completed", "Cancelled"],
        "Ready for Collection": ["Completed", "Cancelled"],
        "Shipped": ["Completed"],
    }
    return new_status in valid_transitions.get(current_status, [])


@router.get("/products", response_model=list[AdminProductResponse])
async def list_products(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """List all products with stock details."""
    result = await db.execute(select(Product).order_by(Product.name))
    products = result.scalars().all()
    return [build_product_response(p) for p in products]


@router.post("/products", response_model=AdminProductResponse)
async def create_product(
    product_data: AdminProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """Add a new product to the inventory."""
    try:
        sku = generate_sku()
        product = Product(
            sku=sku,
            name=product_data.name,
            description=product_data.description,
            image_url=product_data.image_url,
            physical_stock=product_data.stock_quantity,
            reserved_stock=0,
            price=product_data.price,
            version=1
        )
        db.add(product)
        await db.commit()
        await db.refresh(product)
        logger.info(f"Product {sku} created successfully")
        return build_product_response(product)
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/products/{product_id}", response_model=AdminProductResponse)
async def update_product(
    product_id: int,
    product_data: AdminProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """
    Update product details or adjust stock levels.

    If stock_adjustment is provided, it will be added to current physical_stock.
    Positive values add stock, negative values subtract stock.
    """
    try:
        result = await db.execute(select(Product).filter(Product.id == product_id))
        product = result.scalar_one_or_none()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        if product_data.name is not None:
            product.name = product_data.name
        if product_data.description is not None:
            product.description = product_data.description
        if product_data.image_url is not None:
            product.image_url = product_data.image_url
        if product_data.category is not None:
            product.category = product_data.category
        if product_data.price is not None:
            product.price = product_data.price

        # Handle stock adjustment (add or subtract from current)
        if product_data.stock_adjustment is not None:
            new_stock = product.physical_stock + product_data.stock_adjustment
            if new_stock < 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot reduce stock below 0. Current: {product.physical_stock}, Adjustment: {product_data.stock_adjustment}"
                )
            product.physical_stock = new_stock

        product.version += 1

        await db.commit()
        await db.refresh(product)
        logger.info(f"Product {product_id} updated successfully")
        return build_product_response(product)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders", response_model=list[AdminOrderResponse])
async def list_all_orders(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """Fetch all orders with associated items and payment details."""
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payments)
        )
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    return [build_admin_order_response(order) for order in orders]


@router.get("/orders/{order_id}", response_model=AdminOrderResponse)
async def get_order_details(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """Fetch a specific order's full details including payment proof and item list."""
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payments)
        )
        .filter(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return build_admin_order_response(order)


@router.patch("/orders/{order_id}", response_model=AdminOrderResponse)
async def update_order(
    order_id: int,
    order_data: AdminOrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """Update order status, remark, and/or items."""
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payments)
        )
        .filter(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Handle status update
    if order_data.status is not None:
        new_status = order_data.status.value

        # Validate status transition
        if not validate_status_transition(order.status, new_status):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status transition from '{order.status}' to '{new_status}'"
            )

        order.status = new_status

    elif order_data.payment_status is not None:
        order.status = order_data.payment_status.value

    # Handle remark update
    if order_data.remark is not None:
        order.remark = order_data.remark

    # Handle items update (edit order)
    if order_data.items is not None:
        # Only allow editing pending orders
        if order.status not in [
            OrderStatusEnum.PENDING_PAYMENT.value,
            OrderStatusEnum.PAYMENT_UNDER_REVIEW.value,
        ]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot edit items for order with status '{order.status}'"
            )

        # Get current item quantities for stock adjustment
        original_items = {item.product_id: item.quantity for item in order.items}

        # Release old stock
        for item in order.items:
            released = await StockReservationService.release_stock(
                db, item.product_id, item.quantity
            )
            if not released:
                await db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to release stock for product {item.product_id}"
                )

        # Delete old order items
        for item in order.items:
            await db.delete(item)

        # Create new order items with new quantities
        total_price = 0.0
        for item_update in order_data.items:
            # Get product info
            product_result = await db.execute(
                select(Product).filter(Product.id == item_update.product_id)
            )
            product = product_result.scalar_one_or_none()

            if not product:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product {item_update.product_id} not found"
                )

            # Check stock availability
            available = product.physical_stock - product.reserved_stock
            if available < item_update.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for '{product.name}'. Available: {available}"
                )

            # Reserve new stock
            reserved = await StockReservationService.reserve_stock(
                db, item_update.product_id, item_update.quantity
            )
            if not reserved:
                await db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to reserve stock for product {item_update.product_id}"
                )

            # Create order item
            new_item = OrderItem(
                order_id=order.id,
                product_id=item_update.product_id,
                quantity=item_update.quantity,
                unit_price=float(product.price)
            )
            db.add(new_item)
            total_price += product.price * item_update.quantity

        # Recalculate total price
        if order.applied_promo_id:
            # Get promo info
            promo_result = await db.execute(
                select(PromoCode).filter(PromoCode.id == order.applied_promo_id)
            )
            promo = promo_result.scalar_one_or_none()
            if promo:
                if promo.discount_type == "percentage":
                    discount = total_price * (promo.value / 100)
                else:
                    discount = min(promo.value, total_price)
                order.discount_amount = discount
                order.total_price = round(total_price - discount, 2)
            else:
                order.total_price = round(total_price, 2)
        else:
            order.total_price = round(total_price, 2)

    # STOCK DEDUCTION LOGIC - Admin only
    if order_data.status is not None:
        new_status = order_data.status.value

        # When transitioning to Paid, commit stock
        if new_status == OrderStatusEnum.PAID.value:
            for item in order.items:
                committed = await StockReservationService.commit_reservation(
                    db, item.product_id, item.quantity
                )
                if not committed:
                    await db.rollback()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to commit stock for product {item.product_id}"
                    )

        # When cancelling, release stock
        elif new_status == OrderStatusEnum.CANCELLED.value:
            for item in order.items:
                released = await StockReservationService.release_stock(
                    db, item.product_id, item.quantity
                )
                if not released:
                    await db.rollback()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to release stock for product {item.product_id}"
                    )

    await db.commit()

    # Reload order with relationships
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payments)
        )
        .filter(Order.id == order_id)
    )
    order = result.scalar_one()
    return build_admin_order_response(order)


@router.patch("/orders/{order_id}/verify", response_model=VerifyPaymentResponse)
async def verify_payment(
    order_id: int,
    verify_data: VerifyPaymentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """
    Admin endpoint to verify payment receipts.
    Sets status to 'Paid', then auto-transitions based on delivery method:
    - Delivery: Paid → Preparing
    - Pickup: Paid → Ready for Pickup
    """
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payments)
        )
        .filter(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatusEnum.PAYMENT_UNDER_REVIEW.value:
        raise HTTPException(
            status_code=400,
            detail=f"Order is not under review. Current status: {order.status}"
        )

    if verify_data.action == "approve":
        # Extract item data before async operations to avoid lazy loading issues
        order_items_data = [
            {"product_id": item.product_id, "quantity": item.quantity}
            for item in order.items
        ]
        delivery_method = order.delivery_method
        order_number = order.order_number

        # Commit stock for each item
        for item_data in order_items_data:
            committed = await StockReservationService.commit_reservation(
                db, item_data["product_id"], item_data["quantity"]
            )
            if not committed:
                await db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to deduct stock for product {item_data['product_id']}"
                )

        # First set status to "Paid"
        order.status = OrderStatusEnum.PAID.value
        await db.flush()

        # Immediately auto-transition based on delivery method
        if delivery_method == DeliveryMethod.PICKUP.value:
            new_status = OrderStatusEnum.READY_FOR_PICKUP.value
        else:
            new_status = OrderStatusEnum.PREPARING.value

        # Log the status transition
        await ActivityLogService.log(
            db=db,
            user_id=current_user.id,
            action=ActivityAction.VERIFY_PAYMENT.value,
            entity_type="order",
            entity_id=order_id,
            description=f"Payment verified. Order auto-transitioned to '{new_status}'.",
            extra_data={
                "order_number": order_number,
                "old_status": OrderStatusEnum.PAYMENT_UNDER_REVIEW.value,
                "paid_status_duration": "immediate",
                "final_status": new_status,
                "delivery_method": delivery_method
            }
        )

        # Update to final status
        order.status = new_status

        await db.commit()
        return VerifyPaymentResponse(
            order_id=order.id, order_number=order.order_number, status=order.status,
            action="approve", message=f"Payment verified. Order auto-transitioned to '{new_status}'.", stock_action="deducted"
        )

    elif verify_data.action == "reject":
        # Extract item data before async operations
        order_items_data = [
            {"product_id": item.product_id, "quantity": item.quantity}
            for item in order.items
        ]

        order.status = OrderStatusEnum.CANCELLED.value
        for item_data in order_items_data:
            released = await StockReservationService.release_stock(
                db, item_data["product_id"], item_data["quantity"]
            )
            if not released:
                await db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to release stock for product {item_data['product_id']}"
                )
        await db.commit()
        return VerifyPaymentResponse(
            order_id=order.id, order_number=order.order_number, status=order.status,
            action="reject", message="Payment rejected. Stock released.", stock_action="released"
        )

    raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'.")


@router.post("/inventory/restock", response_model=RestockResponse)
async def restock_inventory(
    restock_data: RestockRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """Admin endpoint to add stock using atomic increment."""
    result = await db.execute(select(Product).filter(Product.id == restock_data.product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if restock_data.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")

    previous_stock = product.physical_stock

    success = await StockReservationService.restock(db, restock_data.product_id, restock_data.quantity)
    if not success:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to restock")

    await db.refresh(product)

    return RestockResponse(
        product_id=product.id, sku=product.sku, name=product.name,
        previous_stock=previous_stock, added_quantity=restock_data.quantity,
        new_stock=product.physical_stock
    )


@router.post("/orders/{order_id}/confirm-payment", response_model=AdminOrderResponse)
async def confirm_payment(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """
    Admin endpoint to confirm payment.
    Sets status to 'Paid', then auto-transitions based on delivery method:
    - Delivery: Paid → Preparing
    - Pickup: Paid → Ready for Pickup
    """
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payments)
        )
        .filter(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatusEnum.PAYMENT_UNDER_REVIEW.value:
        raise HTTPException(
            status_code=400,
            detail=f"Order is not under review. Current status: {order.status}"
        )

    # Extract item data before async operations to avoid lazy loading issues
    order_items_data = [
        {"product_id": item.product_id, "quantity": item.quantity}
        for item in order.items
    ]
    delivery_method = order.delivery_method

    # Deduct physical_stock and reserved_stock for each item
    for item_data in order_items_data:
        success = await StockReservationService.commit_reservation(
            db, item_data["product_id"], item_data["quantity"]
        )
        if not success:
            await db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Failed to commit stock for product {item_data['product_id']}"
            )

    # First set status to "Paid"
    order.status = OrderStatusEnum.PAID.value
    await db.flush()

    # Immediately auto-transition based on delivery method
    if delivery_method == DeliveryMethod.PICKUP.value:
        new_status = OrderStatusEnum.READY_FOR_PICKUP.value
    else:
        new_status = OrderStatusEnum.PREPARING.value

    # Log the status transition
    await ActivityLogService.log(
        db=db,
        user_id=current_user.id,
        action=ActivityAction.VERIFY_PAYMENT.value,
        entity_type="order",
        entity_id=order_id,
        description=f"Payment verified. Order auto-transitioned to '{new_status}'.",
        extra_data={
            "order_number": order.order_number,
            "old_status": OrderStatusEnum.PAYMENT_UNDER_REVIEW.value,
            "paid_status_duration": "immediate",
            "final_status": new_status,
            "delivery_method": delivery_method
        }
    )

    # Update to final status
    order.status = new_status

    await db.commit()

    # Reload order with relationships
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payments)
        )
        .filter(Order.id == order_id)
    )
    order = result.scalar_one()
    return build_admin_order_response(order)


@router.post("/orders/{order_id}/reject-payment")
async def reject_payment(
    order_id: int,
    reject_data: RejectPaymentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """
    Admin endpoint to reject a payment.
    Sets order status to 'Payment Rejected' and stores the rejection reason.
    Salesman can then re-upload a new payment proof.
    """
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payments)
        )
        .filter(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status not in [
        OrderStatusEnum.PAYMENT_UNDER_REVIEW.value,
        OrderStatusEnum.PAYMENT_REJECTED.value,  # Can reject again with new reason
    ]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject payment for order with status '{order.status}'"
        )

    # Update order status to Payment Rejected
    order.status = OrderStatusEnum.PAYMENT_REJECTED.value

    # Update the latest payment record with rejection reason
    if order.payments:
        latest_payment = max(order.payments, key=lambda p: p.uploaded_at)
        latest_payment.rejection_reason = reject_data.reason
        latest_payment.rejected_at = datetime.utcnow()

    await db.commit()

    # Reload order with relationships
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payments)
        )
        .filter(Order.id == order_id)
    )
    order = result.scalar_one()

    return {
        "order_id": order.id,
        "order_number": order.order_number,
        "status": order.status,
        "rejection_reason": reject_data.reason,
        "message": "Payment rejected. Salesman can upload a new payment proof."
    }


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """Admin endpoint providing global dashboard summary with order stats and low-stock alerts."""
    orders_result = await db.execute(select(Order))
    all_orders = orders_result.scalars().all()

    total_orders = len(all_orders)
    pending_orders = sum(1 for o in all_orders if o.status in [
        OrderStatusEnum.PENDING_PAYMENT.value,
        OrderStatusEnum.PAYMENT_UNDER_REVIEW.value
    ])
    paid_orders = sum(1 for o in all_orders if o.status == OrderStatusEnum.PAID.value)
    cancelled_orders = sum(1 for o in all_orders if o.status == OrderStatusEnum.CANCELLED.value)

    products_result = await db.execute(select(Product))
    all_products = products_result.scalars().all()

    low_stock_alerts = [
        LowStockProduct(
            id=p.id, sku=p.sku, name=p.name,
            physical_stock=p.physical_stock, reserved_stock=p.reserved_stock,
            available_stock=p.physical_stock - p.reserved_stock,
            threshold=LOW_STOCK_THRESHOLD
        )
        for p in all_products if (p.physical_stock - p.reserved_stock) <= LOW_STOCK_THRESHOLD
    ]

    total_revenue = sum(o.total_price for o in all_orders if o.status == OrderStatusEnum.PAID.value)

    # Calculate today's sales
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_orders = [o for o in all_orders if o.created_at and o.created_at >= today_start]
    today_sales = sum(o.total_price for o in today_orders if o.status == OrderStatusEnum.PAID.value)

    return DashboardSummaryResponse(
        total_orders=total_orders,
        today_sales=today_sales,
        pending_orders=pending_orders,
        paid_orders=paid_orders,
        cancelled_orders=cancelled_orders,
        low_stock_alerts=low_stock_alerts,
        total_revenue=total_revenue
    )


@router.post("/orders/{order_id}/cancel", response_model=ForceCancelResponse)
async def force_cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """
    Admin endpoint to force cancel an order.
    Releases reserved stock back to available inventory atomically.
    """
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).filter(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Cannot cancel already cancelled or completed orders
    if order.status == OrderStatusEnum.CANCELLED.value:
        raise HTTPException(status_code=400, detail="Order is already cancelled")

    if order.status == OrderStatusEnum.PAID.value:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel a paid order. Process a refund instead."
        )

    # Release stock for all order items atomically
    failed_products = await StockReservationService.release_order_stock(db, list(order.items))

    if failed_products:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to release stock for products: {failed_products}"
        )

    # Update order status to cancelled
    order.status = OrderStatusEnum.CANCELLED.value

    await db.commit()

    return ForceCancelResponse(
        order_id=order.id,
        order_number=order.order_number,
        status=order.status,
        message="Order cancelled successfully. Stock has been released.",
        stock_released=True
    )


@router.post("/orders/{order_id}/approve-cancel", response_model=ForceCancelResponse)
async def approve_cancel_request(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """
    Admin endpoint to approve a staff's cancel request.
    Releases reserved stock and sets order to cancelled.
    """
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).filter(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatusEnum.CANCEL_REQUESTED.value:
        raise HTTPException(
            status_code=400,
            detail=f"Order is not in cancel requested status. Current: {order.status}"
        )

    # Release stock for all order items atomically
    failed_products = await StockReservationService.release_order_stock(db, list(order.items))

    if failed_products:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to release stock for products: {failed_products}"
        )

    # Update order status to cancelled
    order.status = OrderStatusEnum.CANCELLED.value

    await db.commit()

    return ForceCancelResponse(
        order_id=order.id,
        order_number=order.order_number,
        status=order.status,
        message="Cancel request approved. Order cancelled and stock released.",
        stock_released=True
    )


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """Admin endpoint to get all registered users with their role and status."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            status=UserStatus.ACTIVE.value if user.is_active == 1 else UserStatus.SUSPENDED.value,
            is_active=user.is_active,
            is_superadmin=user.is_superadmin,
            created_at=user.created_at
        )
        for user in users
    ]


@router.patch("/users/{user_id}/status", response_model=UserStatusUpdateResponse)
async def toggle_user_status(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """Admin endpoint to toggle a user's status between Active and Suspended."""
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from modifying their own status
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot modify your own status")

    # Toggle status
    old_status = user.is_active
    new_status = 0 if user.is_active == 1 else 1
    user.is_active = new_status

    await db.flush()

    # Audit log the status change
    status_str = UserStatus.ACTIVE.value if new_status == 1 else UserStatus.SUSPENDED.value
    await ActivityLogService.log_user_status_change(
        db=db,
        changed_by_user_id=current_user.id,
        target_user_id=user.id,
        target_username=user.username,
        new_status=status_str,
        changed_by_username=current_user.username
    )

    await db.commit()
    await db.refresh(user)

    action = "activated" if new_status == 1 else "suspended"
    message = f"User {user.username} has been {action}"

    return UserStatusUpdateResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        status=status_str,
        message=message
    )


@router.post("/create-admin", response_model=CreateAdminResponse)
async def create_admin_user(
    admin_data: CreateAdminRequest,
    db: AsyncSession = Depends(get_db),
    initial_admin: User = Depends(require_initial_admin)
):
    """
    Create a new user with Admin role.

    SECURITY: Only the Initial Admin (user ID 1) can call this endpoint.
    Standard admins will receive 403 Forbidden.

    Args:
        admin_data: Username, email, and password for the new admin

    Returns:
        Created admin user information
    """
    # Check if username already exists
    result = await db.execute(select(User).filter(User.username == admin_data.username))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Check if email already exists
    result = await db.execute(select(User).filter(User.email == admin_data.email))
    existing_email = result.scalar_one_or_none()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")

    # Validate password
    if not admin_data.password or len(admin_data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    # Create new admin user
    hashed_password = hash_password(admin_data.password)
    new_admin = User(
        username=admin_data.username,
        email=admin_data.email,
        hashed_password=hashed_password,
        role="admin",
        is_active=1
    )
    db.add(new_admin)
    await db.flush()

    # Audit log the admin creation
    await ActivityLogService.log_admin_created(
        db=db,
        created_by_user_id=initial_admin.id,
        new_admin_id=new_admin.id,
        new_admin_username=new_admin.username
    )

    await db.commit()
    await db.refresh(new_admin)

    logger.info(f"New admin user created: {new_admin.username} by Initial Admin")

    return CreateAdminResponse(
        id=new_admin.id,
        username=new_admin.username,
        email=new_admin.email,
        role=new_admin.role,
        status=UserStatus.ACTIVE.value,
        message=f"Admin user '{new_admin.username}' created successfully"
    )


@router.patch("/users/{user_id}/promote", response_model=PromoteUserResponse)
async def promote_user_to_admin(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    initial_admin: User = Depends(require_initial_admin)
):
    """
    Promote an existing user from Salesman to Admin role.

    SECURITY: Only the Initial Admin (user ID 1) can call this endpoint.
    Standard admins will receive 403 Forbidden.

    Args:
        user_id: ID of the user to promote

    Returns:
        Updated user information with new role
    """
    # Cannot promote self
    if user_id == initial_admin.id:
        raise HTTPException(status_code=400, detail="Cannot promote yourself")

    # Find the user to promote
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if user is already an admin
    if user.role == "admin":
        raise HTTPException(status_code=400, detail="User is already an admin")

    # Promote user to admin
    old_role = user.role
    user.role = "admin"
    await db.flush()

    # Audit log the promotion
    await ActivityLogService.log_user_promoted(
        db=db,
        promoted_by_user_id=initial_admin.id,
        promoted_user_id=user.id,
        promoted_username=user.username,
        promoted_by_username=initial_admin.username
    )

    await db.commit()
    await db.refresh(user)

    logger.info(f"User {user.username} promoted to admin by Initial Admin")

    return PromoteUserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        status=UserStatus.ACTIVE.value if user.is_active == 1 else UserStatus.SUSPENDED.value,
        message=f"User '{user.username}' has been promoted to Admin"
    )


# Notification Service for simulating customer notifications
class NotificationService:
    """Mock notification service for customer updates."""

    @staticmethod
    def notify_order_update(order_number: str, customer_name: str, new_status: str, delivery_method: str) -> dict:
        """
        Simulate sending a notification to customer.
        In production, this would integrate with SMS, email, or push notification services.
        """
        notification_message = {
            "order_number": order_number,
            "customer_name": customer_name,
            "new_status": new_status,
            "delivery_method": delivery_method,
            "notification_type": "order_status_update",
        }

        # Log the notification (simulated)
        logger.info(
            f"[NOTIFICATION] Order {order_number} ({delivery_method}): "
            f"Customer '{customer_name}' notified of status change to '{new_status}'"
        )

        # Simulate notification content based on status
        if new_status == OrderStatusEnum.SHIPPED.value:
            notification_message["message"] = (
                f"Great news! Your order {order_number} has been shipped and is on its way to you."
            )
        elif new_status == OrderStatusEnum.READY_FOR_COLLECTION.value:
            notification_message["message"] = (
                f"Your order {order_number} is ready for collection! "
                f"Please visit us to pick up your items."
            )
        elif new_status == OrderStatusEnum.READY_FOR_PICKUP.value:
            notification_message["message"] = (
                f"Your order {order_number} is ready for pickup! "
                f"Please visit us to collect your items."
            )
        elif new_status == OrderStatusEnum.COMPLETED.value:
            notification_message["message"] = (
                f"Your order {order_number} has been completed. Thank you for your purchase!"
            )
        else:
            notification_message["message"] = (
                f"Your order {order_number} status has been updated to: {new_status}"
            )

        return notification_message


@router.post("/orders/{order_id}/done-preparing", response_model=AdminOrderResponse)
async def done_preparing(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """
    Mark an order as done preparing.

    Based on delivery method:
    - Delivery: Status -> Shipped
    - Pickup: Status -> Ready for Collection

    Notifies the customer of the status change.
    """
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payments)
        )
        .filter(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatusEnum.PREPARING.value:
        raise HTTPException(
            status_code=400,
            detail=f"Order is not in 'Preparing' status. Current status: {order.status}"
        )

    # Determine new status based on delivery method
    if order.delivery_method == DeliveryMethod.DELIVERY.value:
        new_status = OrderStatusEnum.SHIPPED.value
    elif order.delivery_method == DeliveryMethod.PICKUP.value:
        new_status = OrderStatusEnum.READY_FOR_COLLECTION.value
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown delivery method: {order.delivery_method}"
        )

    # Update status
    old_status = order.status
    order.status = new_status

    # Log the status change
    await ActivityLogService.log(
        db=db,
        user_id=current_user.id,
        action=ActivityAction.UPDATE_ORDER.value,
        entity_type="order",
        entity_id=order_id,
        description=f"Order marked as done preparing. Status changed from '{old_status}' to '{new_status}'.",
        extra_data={
            "order_number": order.order_number,
            "old_status": old_status,
            "new_status": new_status,
            "delivery_method": order.delivery_method
        }
    )

    await db.commit()

    # Notify customer (simulated)
    notification = NotificationService.notify_order_update(
        order_number=order.order_number,
        customer_name=order.customer_name,
        new_status=new_status,
        delivery_method=order.delivery_method
    )
    logger.info(f"Notification sent: {notification}")

    # Reload order with relationships
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payments)
        )
        .filter(Order.id == order_id)
    )
    order = result.scalar_one()

    return build_admin_order_response(order)