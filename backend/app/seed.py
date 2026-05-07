from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import hashlib

from app.models import User, UserRole


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


async def seed_default_users(db: AsyncSession) -> None:
    """Seed default admin and staff users if they don't exist."""
    admin_exists = await db.execute(select(User).filter(User.username == "admin"))
    if not admin_exists.scalar_one_or_none():
        admin = User(
            username="admin",
            email="admin@flashorder.com",
            hashed_password=hash_password("admin123"),
            role=UserRole.ADMIN.value,
            is_active=1
        )
        db.add(admin)

    staff_exists = await db.execute(select(User).filter(User.username == "staff"))
    if not staff_exists.scalar_one_or_none():
        staff = User(
            username="staff",
            email="staff@flashorder.com",
            hashed_password=hash_password("staff123"),
            role=UserRole.STAFF.value,
            is_active=1
        )
        db.add(staff)

    await db.commit()