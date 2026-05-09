from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from datetime import datetime
import os
import uuid

from ..database import get_db
from ..models import Order, OrderItem, OrderStatusEnum, Payment
from ..schemas import PaymentResponse, OrderItemHistory
from ..auth.dependencies import get_current_active_user, CurrentUser

router = APIRouter(prefix="/payments", tags=["payments"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "uploads")


@router.get("/", response_model=list[PaymentResponse])
async def list_payments(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """List all payments with order details and items."""
    result = await db.execute(
        select(Payment)
        .options(
            joinedload(Payment.order)
            .joinedload(Order.items)
            .joinedload(OrderItem.product)
        )
        .order_by(Payment.uploaded_at.desc())
    )
    payments = result.scalars().unique().all()

    return [
        PaymentResponse(
            id=p.id,
            order_id=p.order_id,
            order_number=p.order.order_number if p.order else None,
            receipt_url=p.receipt_url,
            uploaded_at=p.uploaded_at,
            status=p.order.status if p.order else "Unknown",
            order_items=[
                OrderItemHistory(
                    product_name=item.product.name if item.product else "Unknown",
                    product_image_url=item.product.image_url if item.product else None,
                    quantity=item.quantity,
                    unit_price=float(item.unit_price)
                )
                for item in (p.order.items if p.order else [])
            ]
        )
        for p in payments
    ]


@router.get("/history", response_model=list[PaymentResponse])
async def payment_history(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Get comprehensive payment history with full order details."""
    result = await db.execute(
        select(Payment)
        .options(
            joinedload(Payment.order)
            .joinedload(Order.items)
            .joinedload(OrderItem.product)
        )
        .order_by(Payment.uploaded_at.desc())
        .limit(50)
    )
    payments = result.scalars().unique().all()

    return [
        PaymentResponse(
            id=p.id,
            order_id=p.order_id,
            order_number=p.order.order_number if p.order else None,
            receipt_url=p.receipt_url,
            uploaded_at=p.uploaded_at,
            status=p.order.status if p.order else "Unknown",
            order_items=[
                OrderItemHistory(
                    product_name=item.product.name if item.product else "Unknown",
                    product_image_url=item.product.image_url if item.product else None,
                    quantity=item.quantity,
                    unit_price=float(item.unit_price)
                )
                for item in (p.order.items if p.order else [])
            ]
        )
        for p in payments
    ]


@router.post("/{order_id}/upload")
async def upload_receipt(
    order_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    if file.content_type not in ["image/jpeg", "image/png", "application/pdf"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPG, PNG, and PDF are allowed")

    result = await db.execute(select(Order).filter(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != OrderStatusEnum.PENDING_PAYMENT.value:
        raise HTTPException(status_code=400, detail=f"Order is not pending payment. Current status: {order.status}")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4().hex}.{file_ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    payment = Payment(
        order_id=order_id,
        receipt_url=f"/uploads/{filename}",
        uploaded_at=datetime.utcnow()
    )
    db.add(payment)
    order.status = OrderStatusEnum.PAYMENT_UNDER_REVIEW.value

    await db.commit()
    await db.refresh(payment)
    return payment
