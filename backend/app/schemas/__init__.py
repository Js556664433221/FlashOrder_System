from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    PENDING_PAYMENT = "Pending Payment"
    PAYMENT_UNDER_REVIEW = "Payment Under Review"
    PAYMENT_REJECTED = "Payment Rejected"
    PAID = "Paid"
    PREPARING = "Preparing"
    READY_FOR_PICKUP = "Ready for Pickup"
    SHIPPED = "Shipped"
    COMPLETED = "Completed"
    CANCEL_REQUESTED = "Cancel Requested"
    CANCELLED = "Cancelled"


class DeliveryMethod(str, Enum):
    DELIVERY = "Delivery"
    PICKUP = "Pickup"


class AdminOrderStatus(str, Enum):
    PENDING = "Pending Payment"
    PAYMENT_UNDER_REVIEW = "Payment Under Review"
    PAYMENT_REJECTED = "Payment Rejected"
    PAID = "Paid"
    PREPARING = "Preparing"
    READY_FOR_PICKUP = "Ready for Pickup"
    SHIPPED = "Shipped"
    COMPLETED = "Completed"
    CANCEL_REQUESTED = "Cancel Requested"
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
    image_url: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None


class AdminProductResponse(BaseModel):
    id: int
    sku: str
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    physical_stock: int
    reserved_stock: int
    available_stock: int
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
    product_sku: Optional[str] = None
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
    customer_name: str
    delivery_method: DeliveryMethod = DeliveryMethod.PICKUP
    address: Optional[str] = None
    promo_code: Optional[str | list[str]] = None
    remark: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    order_number: str
    or_number: str
    customer_name: str
    delivery_method: str
    address: Optional[str] = None
    total_price: float
    discount_amount: float = 0.0
    applied_promo_id: Optional[int] = None
    status: str
    remark: Optional[str] = None
    user_id: int
    created_at: datetime
    items: list[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


# AdminPaymentResponse must be defined before AdminOrderResponse due to forward reference
class OrderItemUpdate(BaseModel):
    product_id: int
    quantity: int


class AdminOrderUpdate(BaseModel):
    status: Optional[AdminOrderStatus] = None
    payment_status: Optional[AdminPaymentStatus] = None
    remark: Optional[str] = None
    items: Optional[list[OrderItemUpdate]] = None


class AdminPaymentResponse(BaseModel):
    id: int
    order_id: int
    receipt_url: str
    rejection_reason: Optional[str] = None
    rejected_at: Optional[datetime] = None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminOrderResponse(BaseModel):
    id: int
    order_number: str
    total_price: float
    status: str
    remark: Optional[str] = None
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


class RejectPaymentRequest(BaseModel):
    reason: str


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
    today_sales: float
    pending_orders: int
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


class DiscountType(str, Enum):
    PERCENTAGE = "percentage"
    FLAT = "flat"


class PromoCodeBase(BaseModel):
    code: str
    discount_type: DiscountType
    value: float
    expiry_date: Optional[datetime] = None
    is_active: bool = True


class PromoCodeCreate(PromoCodeBase):
    pass


class PromoCodeUpdate(BaseModel):
    code: Optional[str] = None
    discount_type: Optional[DiscountType] = None
    value: Optional[float] = None
    expiry_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class PromoCodeResponse(PromoCodeBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromoCodeValidationResult(BaseModel):
    valid: bool
    code: Optional[str] = None
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    message: str


class UserStatus(str, Enum):
    ACTIVE = "Active"
    SUSPENDED = "Suspended"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    status: str
    is_active: int
    is_superadmin: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserStatusUpdateResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    status: str
    message: str

    model_config = ConfigDict(from_attributes=True)


class CreateAdminRequest(BaseModel):
    username: str
    email: str
    password: str


class CreateAdminResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    status: str
    message: str

    model_config = ConfigDict(from_attributes=True)


class PromoteUserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    status: str
    message: str


class PromoStatsResponse(BaseModel):
    id: int
    code: str
    discount_type: str
    value: float
    expiry_date: Optional[datetime] = None
    is_active: bool
    usage_count: int
    total_discount_given: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Customer Profile Schemas
class CustomerProfileCreate(BaseModel):
    name: str
    company_name: Optional[str] = None
    location: Optional[str] = None
    contact_number: str
    email: Optional[str] = None


class CustomerProfileUpdate(BaseModel):
    name: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[str] = None


class CustomerProfileResponse(BaseModel):
    id: int
    salesman_id: int
    name: str
    company_name: Optional[str] = None
    location: Optional[str] = None
    contact_number: str
    email: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)