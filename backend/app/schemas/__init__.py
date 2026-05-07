from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    PENDING_PAYMENT = "Pending Payment"
    PAYMENT_UNDER_REVIEW = "Payment Under Review"
    PAID = "Paid"
    CANCEL_REQUESTED = "Cancel Requested"
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
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AdminProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
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


class OrderItemResponse(BaseModel):
    product_id: int
    product_name: str
    product_image_url: str | None = None
    quantity: int
    unit_price: float

    model_config = ConfigDict(from_attributes=True)


class OrderItemWithProduct(BaseModel):
    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: float
    product_name: str = "Unknown"
    product: "AdminProductResponse"
    stock_status: str = "Unknown"

    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    total_price: float
    status: OrderStatus


class OrderCreate(BaseModel):
    items: list[OrderItemCreate]


class OrderResponse(BaseModel):
    id: int
    order_number: str
    total_price: float
    status: str
    user_id: int
    created_at: datetime
    items: list[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


# AdminPaymentResponse must be defined before AdminOrderResponse due to forward reference
class AdminOrderUpdate(BaseModel):
    status: Optional[AdminOrderStatus] = None
    payment_status: Optional[AdminPaymentStatus] = None


class AdminPaymentResponse(BaseModel):
    id: int
    order_id: int
    receipt_url: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminOrderResponse(BaseModel):
    id: int
    order_number: str
    total_price: float
    status: str
    created_at: datetime
    items: list[OrderItemWithProduct] = []
    payment: Optional[AdminPaymentResponse] = None

    model_config = ConfigDict(from_attributes=True)


class PaymentBase(BaseModel):
    order_id: int
    receipt_url: str


class PaymentCreate(BaseModel):
    order_id: int


class OrderItemHistory(BaseModel):
    product_name: str
    product_image_url: str | None = None
    quantity: int
    unit_price: float

    model_config = ConfigDict(from_attributes=True)


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    order_number: str
    receipt_url: str
    uploaded_at: datetime
    status: str = "Unknown"
    order_items: list[OrderItemHistory] = []

    model_config = ConfigDict(from_attributes=True)


class VerifyPaymentRequest(BaseModel):
    action: str
    notes: Optional[str] = None


class VerifyPaymentResponse(BaseModel):
    order_id: int
    order_number: str
    status: str
    action: str
    message: str
    stock_action: Optional[str] = None


class RestockRequest(BaseModel):
    product_id: int
    quantity: int
    reason: Optional[str] = None


class RestockResponse(BaseModel):
    product_id: int
    sku: str
    name: str
    previous_stock: int
    added_quantity: int
    new_stock: int


class CancelRequestResponse(BaseModel):
    order_id: int
    order_number: str
    status: str
    message: str


class ForceCancelResponse(BaseModel):
    order_id: int
    order_number: str
    status: str
    message: str
    stock_released: bool


class DashboardSummaryResponse(BaseModel):
    total_orders: int
    pending_payments: int
    paid_orders: int
    cancelled_orders: int
    low_stock_alerts: list["LowStockProduct"]
    total_revenue: float


class LowStockProduct(BaseModel):
    id: int
    sku: str
    name: str
    physical_stock: int
    reserved_stock: int
    available_stock: int
    threshold: int = 10


DashboardSummaryResponse.model_rebuild()