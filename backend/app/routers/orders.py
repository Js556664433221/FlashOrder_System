from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from datetime import datetime
import uuid

from ..database import get_db
from ..models import Product, Order, OrderItem, OrderStatusEnum, UserRole
from ..services import StockReservationService
from ..auth.dependencies import get_current_active_user, MockUser
from ..schemas import OrderResponse, OrderItemResponse

router = APIRouter(prefix="/orders", tags=["orders"])


def build_order_response(order: Order) -> dict:
    """Build order response with items and product details."""
    items = []
    if order.items:
        for item in order.items:
            items.append(OrderItemResponse(
                product_id=item.product_id,
                product_name=item.product.name if item.product else "Unknown",
                quantity=item.quantity,
                unit_price=float(item.unit_price)
            ).model_dump())

    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        total_price=float(order.total_price),
        status=order.status,
        user_id=order.user_id,
        created_at=order.created_at,
        items=items
    ).model_dump()


@router.get("/")
async def list_orders(
    db: AsyncSession = Depends(get_db),
    current_user: MockUser = Depends(get_current_active_user)
):
    """List orders with data isolation and full item details."""
    query = select(Order).options(
        joinedload(Order.items).joinedload(OrderItem.product)
    )

    if current_user.role == UserRole.STAFF.value:
        query = query.filter(Order.user_id == current_user.id)

    result = await db.execute(query.order_by(Order.created_at.desc()))
    orders = result.scalars().unique().all()

    return [build_order_response(o) for o in orders]


@router.get("/{order_id}")
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: MockUser = Depends(get_current_active_user)
):
    """Get a single order with ownership check and full item details."""
    result = await db.execute(
        select(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.product))
        .filter(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.role == UserRole.STAFF.value and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied: you can only view your own orders")

    return build_order_response(order)


@router.post("/")
async def create_order(
    order_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: MockUser = Depends(get_current_active_user)
):
    """Create a new order. Staff orders are tagged with their user_id."""
    items = order_data.get("items", [])
    order_number = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
    total_price = 0.0
    order_items_data = []

    for item in items:
        product_id = item.get("product_id")
        quantity = item.get("quantity", 1)

        result = await db.execute(select(Product).filter(Product.id == product_id))
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

        available = product.physical_stock - product.reserved_stock
        reserved = await StockReservationService.reserve_stock(db, product.id, quantity)
        if not reserved:
            await db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for product {product_id}. Available: {available}"
            )

        item_price = product.price * quantity
        total_price += item_price
        order_items_data.append({
            "product_id": product.id,
            "quantity": quantity,
            "unit_price": product.price
        })

    order = Order(
        order_number=order_number,
        total_price=total_price,
        status=OrderStatusEnum.PENDING_PAYMENT.value,
        user_id=current_user.id
    )
    db.add(order)
    await db.flush()

    for item_data in order_items_data:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data["product_id"],
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"]
        )
        db.add(order_item)

    await db.commit()

    # Refetch order with items and products for response using selectinload
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .filter(Order.id == order.id)
    )
    order_with_items = result.scalar_one()

    return build_order_response(order_with_items)


@router.post("/{order_id}/request-cancel")
async def request_cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: MockUser = Depends(get_current_active_user)
):
    """Staff endpoint to request order cancellation."""
    result = await db.execute(select(Order).filter(Order.id == order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied: you can only cancel your own orders")

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
    current_user: MockUser = Depends(get_current_active_user)
):
    """Upload payment for an order."""
    result = await db.execute(select(Order).filter(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.role == UserRole.STAFF.value and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

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