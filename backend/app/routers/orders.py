from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime
import uuid

from ..database import get_db
from ..models import Product, Order, OrderItem, OrderStatusEnum
from ..schemas import OrderCreate, OrderResponse, OrderItemResponse, PaymentResponse

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/", response_model=list[OrderResponse])
async def list_orders(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).options(selectinload(Order.items)))
    orders = result.scalars().all()
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).options(selectinload(Order.items)).filter(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/", response_model=OrderResponse)
async def create_order(order_data: OrderCreate, db: AsyncSession = Depends(get_db)):
    order_number = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
    total_price = 0.0
    order_items_data = []

    for item in order_data.items:
        result = await db.execute(select(Product).filter(Product.id == item.product_id))
        product = result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if product.stock_balance < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name}. Available: {product.stock_balance}, Requested: {item.quantity}"
            )
        await db.execute(
            Product.__table__.update().where(Product.id == product.id).values(stock_balance=Product.stock_balance - item.quantity)
        )
        item_price = product.price * item.quantity
        total_price += item_price
        order_items_data.append({
            "product_id": product.id,
            "quantity": item.quantity,
            "unit_price": product.price
        })

    order = Order(
        order_number=order_number,
        total_price=total_price,
        status=OrderStatusEnum.PENDING_PAYMENT.value
    )
    db.add(order)
    await db.flush()

    for item_data in order_items_data:
        order_item = OrderItem(order_id=order.id, **item_data)
        db.add(order_item)

    await db.commit()

    result = await db.execute(select(Order).options(selectinload(Order.items)).filter(Order.id == order.id))
    order = result.scalar_one()
    return order


@router.post("/{order_id}/upload-payment", response_model=PaymentResponse)
async def upload_payment(order_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).filter(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatusEnum.PENDING_PAYMENT.value:
        raise HTTPException(status_code=400, detail=f"Order is not pending payment. Current status: {order.status}")

    from ..models import Payment
    payment = Payment(
        order_id=order_id,
        receipt_url=f"/uploads/{order_id}/receipt",
        uploaded_at=datetime.utcnow()
    )
    db.add(payment)
    order.status = OrderStatusEnum.PAYMENT_UNDER_REVIEW.value

    await db.commit()
    await db.refresh(payment)
    return payment
