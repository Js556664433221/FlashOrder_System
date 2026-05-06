from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime
import uuid

from ..database import get_db
from ..models import Product, Order, OrderItem, Payment, OrderStatusEnum
from ..schemas import (
    AdminProductCreate, AdminProductUpdate, AdminProductResponse,
    AdminOrderUpdate, AdminOrderResponse, AdminPaymentResponse,
    AdminOrderStatus, AdminPaymentStatus, OrderItemWithProduct
)
from ..services import StockReservationService

router = APIRouter(prefix="/admin", tags=["admin"])


def get_stock_status(order_status: str) -> str:
    """Determine stock status based on order status."""
    if order_status in (
        OrderStatusEnum.PENDING_PAYMENT.value,
        OrderStatusEnum.PAYMENT_UNDER_REVIEW.value,
        AdminOrderStatus.PENDING.value,
    ):
        return "Reserved"
    elif order_status in (
        OrderStatusEnum.PAID.value,
        AdminOrderStatus.COMPLETED.value,
        AdminOrderStatus.SHIPPED.value,
        AdminPaymentStatus.VERIFIED.value,
    ):
        return "Deducted"
    elif order_status in (
        OrderStatusEnum.CANCELLED.value,
        AdminOrderStatus.CANCELLED.value,
        AdminPaymentStatus.REJECTED.value,
    ):
        return "Released"
    return "Unknown"


def generate_sku() -> str:
    """Generate a unique SKU."""
    return f"SKU-{uuid.uuid4().hex[:8].upper()}"


@router.post("/products", response_model=AdminProductResponse)
async def create_product(
    product_data: AdminProductCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add a new product to the inventory."""
    sku = generate_sku()
    product = Product(
        sku=sku,
        name=product_data.name,
        description=product_data.description,
        physical_stock=product_data.stock_quantity,
        reserved_stock=0,
        price=product_data.price,
        version=1
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.patch("/products/{product_id}", response_model=AdminProductResponse)
async def update_product(
    product_id: int,
    product_data: AdminProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update product details or adjust stock levels."""
    result = await db.execute(select(Product).filter(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product_data.name is not None:
        product.name = product_data.name
    if product_data.description is not None:
        product.description = product_data.description
    if product_data.price is not None:
        product.price = product_data.price
    if product_data.stock_quantity is not None:
        product.physical_stock = product_data.stock_quantity

    product.version += 1

    await db.commit()
    await db.refresh(product)
    return product


@router.get("/orders", response_model=list[AdminOrderResponse])
async def list_all_orders(db: AsyncSession = Depends(get_db)):
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

    response = []
    for order in orders:
        items_with_product = [
            OrderItemWithProduct(
                id=item.id,
                order_id=item.order_id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                product=AdminProductResponse(
                    id=item.product.id,
                    sku=item.product.sku,
                    name=item.product.name,
                    description=item.product.description,
                    stock_balance=item.product.physical_stock - item.product.reserved_stock,
                    price=item.product.price,
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
                uploaded_at=latest_payment.uploaded_at
            )

        response.append(AdminOrderResponse(
            id=order.id,
            order_number=order.order_number,
            total_price=order.total_price,
            status=order.status,
            created_at=order.created_at,
            items=items_with_product,
            payment=payment_data
        ))

    return response


@router.get("/orders/{order_id}", response_model=AdminOrderResponse)
async def get_order_details(
    order_id: int,
    db: AsyncSession = Depends(get_db)
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

    items_with_product = [
        OrderItemWithProduct(
            id=item.id,
            order_id=item.order_id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            product=AdminProductResponse(
                id=item.product.id,
                sku=item.product.sku,
                name=item.product.name,
                description=item.product.description,
                stock_balance=item.product.physical_stock - item.product.reserved_stock,
                price=item.product.price,
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
            uploaded_at=latest_payment.uploaded_at
        )

    return AdminOrderResponse(
        id=order.id,
        order_number=order.order_number,
        total_price=order.total_price,
        status=order.status,
        created_at=order.created_at,
        items=items_with_product,
        payment=payment_data
    )


@router.patch("/orders/{order_id}", response_model=AdminOrderResponse)
async def update_order(
    order_id: int,
    order_data: AdminOrderUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update order fulfillment status and/or payment status."""
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

    old_status = order.status

    if order_data.status is not None:
        new_status = order_data.status.value
    elif order_data.payment_status is not None:
        new_status = order_data.payment_status.value
    else:
        new_status = None

    if new_status is not None:
        order.status = new_status

    if new_status in (AdminPaymentStatus.VERIFIED.value, AdminOrderStatus.COMPLETED.value):
        for item in order.items:
            product_id = item.product_id
            committed = await StockReservationService.commit_reservation(db, product_id, item.quantity)
            if not committed:
                await db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to commit stock: insufficient reserved stock for product {product_id}"
                )
    elif new_status == AdminOrderStatus.CANCELLED.value:
        for item in order.items:
            product_id = item.product_id
            released = await StockReservationService.release_stock(db, product_id, item.quantity)
            if not released:
                await db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to release stock: no reserved stock found for product {product_id}"
                )

    await db.commit()

    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payments)
        )
        .filter(Order.id == order_id)
    )
    order = result.scalar_one()

    items_with_product = [
        OrderItemWithProduct(
            id=item.id,
            order_id=item.order_id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            product=AdminProductResponse(
                id=item.product.id,
                sku=item.product.sku,
                name=item.product.name,
                description=item.product.description,
                stock_balance=item.product.physical_stock - item.product.reserved_stock,
                price=item.product.price,
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
            uploaded_at=latest_payment.uploaded_at
        )

    return AdminOrderResponse(
        id=order.id,
        order_number=order.order_number,
        total_price=order.total_price,
        status=order.status,
        created_at=order.created_at,
        items=items_with_product,
        payment=payment_data
    )
