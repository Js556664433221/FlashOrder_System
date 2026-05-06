from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    PENDING_PAYMENT = "Pending Payment"
    PAYMENT_UNDER_REVIEW = "Payment Under Review"
    PAID = "Paid"
    CANCELLED = "Cancelled"


class AdminOrderStatus(str, Enum):
    PENDING = "Pending"
    SHIPPED = "Shipped"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class AdminPaymentStatus(str, Enum):
    UNPAID = "Unpaid"
    VERIFIED = "Verified"
    REJECTED = "Rejected"


class ProductBase(BaseModel):
    sku: str
    name: str
    physical_stock: int
    reserved_stock: int
    price: float
    description: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    version: int

    model_config = ConfigDict(from_attributes=True)


class ProductStockResponse(BaseModel):
    id: int
    sku: str
    name: str
    physical_stock: int
    reserved_stock: int
    available_stock: int
    price: float
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AdminProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock_quantity: int


class AdminProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None


class AdminProductResponse(BaseModel):
    id: int
    sku: str
    name: str
    description: Optional[str] = None
    stock_balance: int
    price: float
    version: int

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


class OrderItemWithProduct(OrderItemResponse):
    product: "AdminProductResponse"
    stock_status: str = "Unknown"

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


class AdminOrderUpdate(BaseModel):
    status: Optional[AdminOrderStatus] = None
    payment_status: Optional[AdminPaymentStatus] = None


class AdminOrderResponse(BaseModel):
    id: int
    order_number: str
    total_price: float
    status: str
    created_at: datetime
    items: list[OrderItemWithProduct] = []
    payment: Optional["AdminPaymentResponse"] = None

    model_config = ConfigDict(from_attributes=True)


class AdminPaymentResponse(BaseModel):
    id: int
    order_id: int
    receipt_url: str
    uploaded_at: datetime

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


AdminOrderResponse.model_rebuild()
