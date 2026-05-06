from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import os
import uuid

from ..database import get_db
from ..models import Order, OrderStatusEnum, Payment
from ..schemas import PaymentResponse

router = APIRouter(prefix="/payments", tags=["payments"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "uploads")


@router.post("/{order_id}/upload", response_model=PaymentResponse)
async def upload_receipt(
    order_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
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
