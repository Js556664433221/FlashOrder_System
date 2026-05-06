"""
Database initialization script.
Creates all tables defined in models.py in the local PostgreSQL database.
Can optionally seed sample data.
"""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import text, Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
import enum

Base = declarative_base()


class OrderStatusEnum(str, enum.Enum):
    PENDING_PAYMENT = "Pending Payment"
    PAYMENT_UNDER_REVIEW = "Payment Under Review"
    PAID = "Paid"
    CANCELLED = "Cancelled"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    stock_balance = Column(Integer, nullable=False, default=0)
    price = Column(Float, nullable=False)
    version = Column(Integer, nullable=False, default=1)

    order_items = relationship("OrderItem", back_populates="product")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, index=True, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String(50), default=OrderStatusEnum.PENDING_PAYMENT.value, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")


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
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="payments")


DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql+asyncpg://postgres:postgres@localhost:5432/flashorder"

SAMPLE_PRODUCTS = [
    {"sku": "SKU001", "name": "Wireless Mouse", "stock_balance": 50, "price": 29.99},
    {"sku": "SKU002", "name": "Mechanical Keyboard", "stock_balance": 30, "price": 89.99},
    {"sku": "SKU003", "name": "USB-C Hub", "stock_balance": 25, "price": 49.99},
    {"sku": "SKU004", "name": "Webcam HD", "stock_balance": 40, "price": 59.99},
    {"sku": "SKU005", "name": "Monitor Stand", "stock_balance": 15, "price": 39.99},
]


async def create_tables(drop_existing: bool = False):
    """Create all tables in the database."""
    engine = create_async_engine(DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        if drop_existing:
            await conn.run_sync(Base.metadata.drop_all)
            print("Dropped all existing tables.")
        await conn.run_sync(Base.metadata.create_all)
        print("All tables created successfully!")


async def seed_sample_data():
    """Insert sample products into the database."""
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        for product in SAMPLE_PRODUCTS:
            await conn.execute(
                text("""
                    INSERT INTO products (sku, name, stock_balance, price, version)
                    VALUES (:sku, :name, :stock_balance, :price, 1)
                    ON CONFLICT (sku) DO NOTHING
                """),
                product
            )
        print(f"Inserted {len(SAMPLE_PRODUCTS)} sample products.")


async def init_db(drop_existing: bool = False, seed_data: bool = True):
    """Initialize the database."""
    await create_tables(drop_existing=drop_existing)
    if seed_data:
        await seed_sample_data()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Initialize the database")
    parser.add_argument("--drop", action="store_true", help="Drop existing tables first")
    parser.add_argument("--no-seed", action="store_true", help="Skip seeding sample data")
    args = parser.parse_args()

    asyncio.run(init_db(drop_existing=args.drop, seed_data=not args.no_seed))


if __name__ == "__main__":
    main()
