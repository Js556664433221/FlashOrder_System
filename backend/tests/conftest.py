"""
Test configuration and fixtures for FlashOrder API tests.

Provides:
- Test database session
- Mock user fixtures
- Test client setup
- Sample data seeding
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import patch

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from httpx import AsyncClient, ASGITransport

# Import app and models
from app.main import app
from app.database import Base, get_db
from app.models import User, Order, OrderItem, Product, PromoCode, ActivityLog
from app.models.models import UserRole, OrderStatusEnum, DeliveryMethod
from app.auth.utils import hash_password


# ============================================================
# Test Database Setup
# ============================================================

# Use SQLite for testing (in-memory)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def async_engine():
    """Create async test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    async_session = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ============================================================
# User Fixtures
# ============================================================

@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create admin user."""
    user = User(
        username="admin",
        email="admin@test.com",
        hashed_password=hash_password("admin123"),
        role=UserRole.ADMIN.value,
        is_active=1,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def salesman_a(db_session: AsyncSession) -> User:
    """Create Salesman A user."""
    user = User(
        username="salesman_a",
        email="salesman_a@test.com",
        hashed_password=hash_password("password123"),
        role=UserRole.SALESMAN.value,
        is_active=1,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def salesman_b(db_session: AsyncSession) -> User:
    """Create Salesman B user."""
    user = User(
        username="salesman_b",
        email="salesman_b@test.com",
        hashed_password=hash_password("password123"),
        role=UserRole.SALESMAN.value,
        is_active=1,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def suspended_salesman(db_session: AsyncSession) -> User:
    """Create suspended salesman user."""
    user = User(
        username="suspended_user",
        email="suspended@test.com",
        hashed_password=hash_password("password123"),
        role=UserRole.SALESMAN.value,
        is_active=0,  # Suspended
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ============================================================
# Product Fixtures
# ============================================================

@pytest.fixture
async def sample_products(db_session: AsyncSession) -> list[Product]:
    """Create sample products for testing."""
    products = [
        Product(
            sku="TEST-001",
            name="Test Product A",
            price=100.00,
            physical_stock=50,
            reserved_stock=0,
            version=1,
        ),
        Product(
            sku="TEST-002",
            name="Test Product B",
            price=200.00,
            physical_stock=30,
            reserved_stock=0,
            version=1,
        ),
        Product(
            sku="TEST-003",
            name="Test Product C",
            price=150.00,
            physical_stock=20,
            reserved_stock=0,
            version=1,
        ),
    ]
    for product in products:
        db_session.add(product)
    await db_session.commit()
    for product in products:
        await db_session.refresh(product)
    return products


# ============================================================
# Order Fixtures
# ============================================================

@pytest.fixture
async def salesman_a_orders(
    db_session: AsyncSession,
    salesman_a: User,
    sample_products: list[Product]
) -> list[Order]:
    """Create 3 orders for Salesman A."""
    orders = []
    for i in range(3):
        order = Order(
            order_number=f"FO-TEST-A-{i+1:04d}",
            or_number=f"OR-TEST-A-{i+1:04d}",
            customer_name=f"Customer A-{i+1}",
            delivery_method=DeliveryMethod.PICKUP.value,
            total_price=sample_products[i % len(sample_products)].price,
            discount_amount=0.0,
            status=OrderStatusEnum.PENDING_PAYMENT.value,
            user_id=salesman_a.id,
        )
        db_session.add(order)
        await db_session.flush()

        # Add order items
        item = OrderItem(
            order_id=order.id,
            product_id=sample_products[i % len(sample_products)].id,
            quantity=1,
            unit_price=sample_products[i % len(sample_products)].price,
        )
        db_session.add(item)
        orders.append(order)

    await db_session.commit()
    for order in orders:
        await db_session.refresh(order)
    return orders


@pytest.fixture
async def salesman_b_orders(
    db_session: AsyncSession,
    salesman_b: User,
    sample_products: list[Product]
) -> list[Order]:
    """Create 2 orders for Salesman B."""
    orders = []
    for i in range(2):
        order = Order(
            order_number=f"FO-TEST-B-{i+1:04d}",
            or_number=f"OR-TEST-B-{i+1:04d}",
            customer_name=f"Customer B-{i+1}",
            delivery_method=DeliveryMethod.DELIVERY.value,
            address="123 Test Street, Test City",
            total_price=sample_products[i % len(sample_products)].price * 2,
            discount_amount=10.0,
            status=OrderStatusEnum.PAID.value if i == 0 else OrderStatusEnum.PENDING_PAYMENT.value,
            user_id=salesman_b.id,
        )
        db_session.add(order)
        await db_session.flush()

        # Add order items
        item = OrderItem(
            order_id=order.id,
            product_id=sample_products[i % len(sample_products)].id,
            quantity=2,
            unit_price=sample_products[i % len(sample_products)].price,
        )
        db_session.add(item)
        orders.append(order)

    await db_session.commit()
    for order in orders:
        await db_session.refresh(order)
    return orders


# ============================================================
# Promo Code Fixtures
# ============================================================

@pytest.fixture
async def sample_promo(db_session: AsyncSession) -> PromoCode:
    """Create sample promo code."""
    promo = PromoCode(
        code="TEST10",
        discount_type="percentage",
        value=10.0,
        is_active=1,
    )
    db_session.add(promo)
    await db_session.commit()
    await db_session.refresh(promo)
    return promo


# ============================================================
# Activity Log Fixtures
# ============================================================

@pytest.fixture
async def activity_logs(
    db_session: AsyncSession,
    salesman_a: User,
    salesman_b: User,
    salesman_a_orders: list[Order],
    salesman_b_orders: list[Order]
) -> list[ActivityLog]:
    """Create sample activity logs."""
    logs = []

    # Logs for Salesman A's orders
    for order in salesman_a_orders:
        log = ActivityLog(
            user_id=salesman_a.id,
            action="CREATE_ORDER",
            entity_type="order",
            entity_id=order.id,
            description=f"Created order {order.order_number}",
            extra_data=None,
        )
        db_session.add(log)
        logs.append(log)

    # Logs for Salesman B's orders
    for order in salesman_b_orders:
        log = ActivityLog(
            user_id=salesman_b.id,
            action="CREATE_ORDER",
            entity_type="order",
            entity_id=order.id,
            description=f"Created order {order.order_number}",
            extra_data=None,
        )
        db_session.add(log)
        logs.append(log)

    await db_session.commit()
    return logs


# ============================================================
# Auth Headers Helpers
# ============================================================

def admin_headers(user_id: int = 1) -> dict:
    """Generate headers for admin user."""
    return {
        "X-Simulated-Role": "admin",
        "X-Simulated-User-Id": str(user_id),
        "X-Simulated-Username": "admin",
    }


def salesman_headers(user_id: int, username: str = "salesman") -> dict:
    """Generate headers for salesman user."""
    return {
        "X-Simulated-Role": "salesman",
        "X-Simulated-User-Id": str(user_id),
        "X-Simulated-Username": username,
    }


@pytest.fixture
def get_admin_headers():
    """Fixture for admin headers."""
    return admin_headers


@pytest.fixture
def get_salesman_headers():
    """Fixture for salesman headers."""
    return salesman_headers
