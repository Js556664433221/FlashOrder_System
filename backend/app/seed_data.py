"""
Seed script to populate the database with sample data for testing.
Run with: python -m app.seed_data
"""
import asyncio
import uuid
from datetime import datetime, timedelta
import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal, engine, Base
from app.models import Product, Order, OrderItem, OrderStatusEnum
from app.seed import hash_password
from app.models import User, UserRole


async def create_sample_products(db):
    """Create 5+ sample products with varying stock levels."""
    products_data = [
        {
            "sku": "SKU-LAPTOP01",
            "name": "MacBook Pro 14-inch",
            "description": "Apple M3 Pro chip, 18GB RAM, 512GB SSD",
            "image_url": "https://example.com/macbook.jpg",
            "physical_stock": 15,
            "reserved_stock": 3,
            "price": 2499.00
        },
        {
            "sku": "SKU-HEADPHONE01",
            "name": "Sony WH-1000XM5",
            "description": "Wireless noise cancelling headphones",
            "image_url": "https://example.com/sony.jpg",
            "physical_stock": 8,
            "reserved_stock": 2,
            "price": 549.00
        },
        {
            "sku": "SKU-MOUSE01",
            "name": "Logitech MX Master 3S",
            "description": "Wireless mouse, ergonomic design",
            "image_url": "https://example.com/mxmaster.jpg",
            "physical_stock": 2,  # Low stock - will trigger alert
            "reserved_stock": 0,
            "price": 189.00
        },
        {
            "sku": "SKU-KEYBOARD01",
            "name": "Keychron K3 Pro",
            "description": "Low profile wireless mechanical keyboard",
            "image_url": "https://example.com/keychron.jpg",
            "physical_stock": 0,  # Out of stock - will trigger alert
            "reserved_stock": 0,
            "price": 279.00
        },
        {
            "sku": "SKU-MONITOR01",
            "name": "Dell UltraSharp 27-inch",
            "description": "4K USB-C Hub Monitor",
            "image_url": "https://example.com/dell.jpg",
            "physical_stock": 25,
            "reserved_stock": 5,
            "price": 899.00
        },
        {
            "sku": "SKU-USBHUB01",
            "name": "USB-C Hub 7-in-1",
            "description": "Multi-port adapter with HDMI and ethernet",
            "image_url": "https://example.com/usbhub.jpg",
            "physical_stock": 3,  # Low stock - will trigger alert
            "reserved_stock": 1,
            "price": 89.00
        },
        {
            "sku": "SKU-WEBCAM01",
            "name": "Logitech Brio 4K",
            "description": "4K Ultra HD webcam with HDR",
            "image_url": "https://example.com/brio.jpg",
            "physical_stock": 12,
            "reserved_stock": 2,
            "price": 349.00
        },
        {
            "sku": "SKU-IPAD01",
            "name": "iPad Pro 12.9-inch",
            "description": "M2 chip, 256GB, Wi-Fi + Cellular",
            "image_url": "https://example.com/ipad.jpg",
            "physical_stock": 4,  # Low stock - will trigger alert
            "reserved_stock": 0,
            "price": 1899.00
        },
    ]

    created_count = 0
    for product_data in products_data:
        existing = await db.execute(
            select(Product).filter(Product.sku == product_data["sku"])
        )
        if not existing.scalar_one_or_none():
            product = Product(**product_data)
            db.add(product)
            created_count += 1

    await db.commit()
    return created_count


async def create_sample_orders(db):
    """Create 10 sample orders with different statuses for today."""
    # Get products
    products_result = await db.execute(select(Product))
    products = products_result.scalars().all()

    if len(products) == 0:
        print("No products found. Please create products first.")
        return 0

    # Get or create a salesman user
    user_result = await db.execute(select(User).filter(User.username == "salesman"))
    user = user_result.scalar_one_or_none()
    if not user:
        user = User(
            username="salesman",
            email="salesman@flashorder.com",
            hashed_password=hash_password("salesman123"),
            role=UserRole.SALESMAN.value,
            is_active=1,
            is_superadmin=0
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Order statuses and customer names for variety
    statuses = [
        OrderStatusEnum.PENDING_PAYMENT.value,
        OrderStatusEnum.PENDING_PAYMENT.value,
        OrderStatusEnum.PAYMENT_UNDER_REVIEW.value,
        OrderStatusEnum.PAYMENT_UNDER_REVIEW.value,
        OrderStatusEnum.PAID.value,
        OrderStatusEnum.PAID.value,
        OrderStatusEnum.PREPARING.value,
        OrderStatusEnum.READY_FOR_PICKUP.value,
        OrderStatusEnum.COMPLETED.value,
        OrderStatusEnum.CANCELLED.value,
    ]

    customer_names = [
        "Ahmad Razali",
        "Siti Nurhaliza",
        "Lim Wei Jie",
        "Nurain Binti Mohammad",
        "Tan Kah Hooi",
        "Aisyah Binti Roslan",
        "Muhammad Faris",
        "Chong Mei Ling",
        "Ahmad Faiz bin Ismail",
        "Nadia Natasha",
    ]

    created_count = 0
    base_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)

    for i in range(10):
        # Generate unique order number
        date_str = datetime.now().strftime("%Y%m%d")
        unique_suffix = uuid.uuid4().hex[:4].upper()
        order_number = f"FO-{date_str}-{unique_suffix}"
        or_number = f"OR-{date_str}-{unique_suffix}"

        # Randomly select 1-3 products for this order
        order_products = random.sample(products, min(random.randint(1, 3), len(products)))

        # Calculate total price
        total_price = sum(p.price for p in order_products)
        quantity = random.randint(1, 2)

        # Create order
        order = Order(
            order_number=order_number,
            or_number=or_number,
            customer_name=customer_names[i],
            delivery_method="Pickup" if i % 2 == 0 else "Delivery",
            address="123 Jalan Utama, Kuala Lumpur" if i % 2 == 1 else None,
            total_price=total_price * quantity,
            discount_amount=0.0,
            status=statuses[i],
            created_at=base_time + timedelta(minutes=i * 45),  # Spread orders throughout the day
            user_id=user.id
        )
        db.add(order)
        await db.flush()

        # Create order items
        for product in order_products:
            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=product.price
            )
            db.add(order_item)

        created_count += 1

    await db.commit()
    return created_count


async def seed_all():
    """Main function to seed all sample data."""
    print("Starting database seed...")

    async with AsyncSessionLocal() as db:
        # Seed products
        print("\n[*] Creating sample products...")
        products_count = await create_sample_products(db)
        print(f"    [+] Created {products_count} products")

        # Seed orders
        print("\n[*] Creating sample orders...")
        orders_count = await create_sample_orders(db)
        print(f"    [+] Created {orders_count} orders")

        print("\n[OK] Database seeding completed!")
        print("\nDashboard should now show:")
        print("    - Today's Sales (from paid orders)")
        print("    - Pending Orders (Pending Payment + Payment Under Review)")
        print("    - Stock Alerts (products with stock < 5)")


if __name__ == "__main__":
    asyncio.run(seed_all())
