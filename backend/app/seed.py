from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib

from app.models import User, UserRole


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


async def seed_default_users(db: AsyncSession) -> None:
    """Seed default admin and salesman users if they don't exist."""
    admin_exists = await db.execute(select(User).filter(User.username == "admin"))
    if not admin_exists.scalar_one_or_none():
        admin = User(
            username="admin",
            email="admin@flashorder.com",
            hashed_password=hash_password("admin123"),
            role=UserRole.ADMIN.value,
            is_active=1,
            is_superadmin=1
        )
        db.add(admin)

    salesman_exists = await db.execute(select(User).filter(User.username == "salesman"))
    if not salesman_exists.scalar_one_or_none():
        salesman = User(
            username="salesman",
            email="salesman@flashorder.com",
            hashed_password=hash_password("salesman123"),
            role=UserRole.SALESMAN.value,
            is_active=1,
            is_superadmin=0
        )
        db.add(salesman)

    await db.commit()