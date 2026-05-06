from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    PENDING_PAYMENT = "Pending Payment"
    PAYMENT_UNDER_REVIEW = "Payment Under Review"
    PAID = "Paid"
    CANCELLED = "Cancelled"


class ProductBase(BaseModel):
    sku: str
    name: str
    stock_balance: int
    price: float


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    unit_price: float


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: Optional[float] = None


class OrderItemResponse(OrderItemBase):
    id: int
    order_id: int

    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    total_price: float
    status: OrderStatus


class OrderCreate(BaseModel):
    items: list[OrderItemCreate]


class OrderResponse(OrderBase):
    id: int
    order_number: str
    created_at: datetime
    items: list[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PaymentBase(BaseModel):
    order_id: int
    receipt_url: str


class PaymentCreate(BaseModel):
    order_id: int


class PaymentResponse(PaymentBase):
    id: int
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)
