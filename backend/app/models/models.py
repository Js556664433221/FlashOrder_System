from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime
import enum
import uuid

from ..database import Base


class UserRole(str, enum.Enum):
    SALESMAN = "salesman"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String(20), nullable=False, default=UserRole.SALESMAN.value)
    is_active = Column(Integer, nullable=False, default=1)
    is_superadmin = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class OrderStatusEnum(str, enum.Enum):
    PENDING_PAYMENT = "Pending Payment"
    PAYMENT_UNDER_REVIEW = "Payment Under Review"
    PAYMENT_REJECTED = "Payment Rejected"
    PAID = "Paid"
    PREPARING = "Preparing"
    READY_TO_SHIP = "Ready to Ship"
    READY_FOR_PICKUP = "Ready for Pickup"
    READY_FOR_COLLECTION = "Ready for Collection"
    SHIPPED = "Shipped"
    COMPLETED = "Completed"
    CANCEL_REQUESTED = "Cancel Requested"
    CANCELLED = "Cancelled"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=True, index=True)
    image_url = Column(String, nullable=True)
    physical_stock = Column(Integer, nullable=False, default=0)
    reserved_stock = Column(Integer, nullable=False, default=0)
    price = Column(Float, nullable=False)
    version = Column(Integer, nullable=False, default=1)

    order_items = relationship("OrderItem", back_populates="product")

    @hybrid_property
    def available_stock(self):
        return self.physical_stock - self.reserved_stock

    @available_stock.expression
    def available_stock(cls):
        return cls.physical_stock - cls.reserved_stock


class DeliveryMethod(str, enum.Enum):
    DELIVERY = "Delivery"
    PICKUP = "Pickup"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, index=True, nullable=False)
    or_number = Column(String, unique=True, index=True, nullable=False)
    customer_name = Column(String, nullable=False)
    delivery_method = Column(String(20), nullable=False, default=DeliveryMethod.PICKUP.value)
    address = Column(String, nullable=True)
    total_price = Column(Float, nullable=False)
    discount_amount = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), default=OrderStatusEnum.PENDING_PAYMENT.value, nullable=False)
    remark = Column(String, nullable=True)  # Admin/order remark field
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    applied_promo_id = Column(Integer, ForeignKey("promo_codes.id"), nullable=True)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    owner = relationship("User")
    applied_promo = relationship("PromoCode", foreign_keys=[applied_promo_id])


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    receipt_url = Column(String, nullable=False)
    rejection_reason = Column(String, nullable=True)  # Reason why payment was rejected
    rejected_at = Column(DateTime, nullable=True)  # When payment was rejected
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="payments")


def generate_order_number() -> str:
    """Generate a unique order number with format FO-YYYYMMDD-XXXX."""
    date_str = datetime.utcnow().strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:4].upper()
    return f"FO-{date_str}-{unique_suffix}"


def generate_or_number() -> str:
    """Generate a unique Official Receipt number with format OR-YYYYMMDD-XXXX."""
    date_str = datetime.utcnow().strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:4].upper()
    return f"OR-{date_str}-{unique_suffix}"


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    discount_type = Column(String(20), nullable=False)  # "percentage" or "flat"
    value = Column(Float, nullable=False)
    expiry_date = Column(DateTime, nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class ActivityLog(Base):
    """Model for tracking user activities in the system."""
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=True)
    description = Column(String, nullable=True)
    extra_data = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class ActivityAction(str, enum.Enum):
    """Enumeration of possible activity actions."""
    CREATE_ORDER = "CREATE_ORDER"
    UPDATE_ORDER = "UPDATE_ORDER"
    CANCEL_ORDER = "CANCEL_ORDER"
    REQUEST_CANCEL = "REQUEST_CANCEL"
    UPLOAD_PAYMENT = "UPLOAD_PAYMENT"
    VERIFY_PAYMENT = "VERIFY_PAYMENT"
    REJECT_PAYMENT = "REJECT_PAYMENT"
    CREATE_PRODUCT = "CREATE_PRODUCT"
    UPDATE_PRODUCT = "UPDATE_PRODUCT"
    RESTOCK_PRODUCT = "RESTOCK_PRODUCT"
    CREATE_PROMO = "CREATE_PROMO"
    UPDATE_PROMO = "UPDATE_PROMO"
    ACTIVATE_PROMO = "ACTIVATE_PROMO"
    DEACTIVATE_PROMO = "DEACTIVATE_PROMO"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    USER_CREATED = "USER_CREATED"
    USER_SUSPENDED = "USER_SUSPENDED"
    USER_ACTIVATED = "USER_ACTIVATED"
    ROLE_CHANGED = "ROLE_CHANGED"
    ADMIN_CREATED = "ADMIN_CREATED"
    USER_PROMOTED = "USER_PROMOTED"


class CustomerProfile(Base):
    """Model for customer profiles managed by salesmen."""
    __tablename__ = "customer_profiles"

    id = Column(Integer, primary_key=True, index=True)
    salesman_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    location = Column(String, nullable=True)
    contact_number = Column(String, nullable=False)
    email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", foreign_keys=[salesman_id])
