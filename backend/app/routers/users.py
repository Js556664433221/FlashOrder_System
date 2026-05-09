"""
User Management Router.

Admin-only CRUD endpoints for managing user accounts.
Only users with 'Admin' role can access these endpoints.
Salesman users will receive a 403 Forbidden error.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

from ..database import get_db
from ..models import User, UserRole
from ..auth.utils import hash_password
from ..auth.dependencies import get_current_admin, CurrentUser

router = APIRouter(prefix="/admin/users", tags=["users"])


class UserBase(BaseModel):
    username: str
    email: str
    role: str


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "salesman"


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    total: int
    users: List[UserResponse]


@router.get("/", response_model=UserListResponse)
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin),
    role_filter: Optional[str] = Query(default=None, description="Filter by role (admin/salesman)"),
    status_filter: Optional[str] = Query(default=None, description="Filter by status (active/suspended)")
):
    """
    List all users.

    **Admin Only**: This endpoint requires Admin role.
    Returns 403 Forbidden if accessed by Salesman.

    Query Parameters:
    - role_filter: Filter by role (admin/salesman)
    - status_filter: Filter by status (active/suspended)
    """
    query = select(User).order_by(desc(User.created_at))

    if role_filter:
        query = query.filter(User.role == role_filter)

    if status_filter:
        if status_filter == "active":
            query = query.filter(User.is_active == 1)
        elif status_filter == "suspended":
            query = query.filter(User.is_active == 0)

    result = await db.execute(query)
    users = result.scalars().all()

    return UserListResponse(
        total=len(users),
        users=[UserResponse.model_validate(u) for u in users]
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """
    Get a specific user by ID.

    **Admin Only**: This endpoint requires Admin role.
    Returns 403 Forbidden if accessed by Salesman.
    """
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse.model_validate(user)


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """
    Create a new user.

    **Admin Only**: This endpoint requires Admin role.
    Returns 403 Forbidden if accessed by Salesman.

    Default role is 'salesman'. To create admin users, explicitly set role='admin'.
    """
    # Validate role
    if user_data.role not in [UserRole.ADMIN.value, UserRole.SALESMAN.value]:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be 'admin' or 'salesman'")

    # Check for duplicate username
    result = await db.execute(select(User).filter(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Username '{user_data.username}' already exists")

    # Check for duplicate email
    result = await db.execute(select(User).filter(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Email '{user_data.email}' already exists")

    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
        is_active=1,
        created_at=datetime.utcnow()
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """
    Update a user.

    **Admin Only**: This endpoint requires Admin role.
    Returns 403 Forbidden if accessed by Salesman.

    All fields are optional - only provided fields will be updated.
    Cannot deactivate the last admin user.
    """
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check for duplicate username if being updated
    if user_data.username and user_data.username != user.username:
        existing = await db.execute(
            select(User).filter(User.username == user_data.username)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Username '{user_data.username}' already exists")

    # Check for duplicate email if being updated
    if user_data.email and user_data.email != user.email:
        existing = await db.execute(
            select(User).filter(User.email == user_data.email)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"Email '{user_data.email}' already exists")

    # Validate role if being updated
    if user_data.role:
        if user_data.role not in [UserRole.ADMIN.value, UserRole.SALESMAN.value]:
            raise HTTPException(status_code=400, detail=f"Invalid role. Must be 'admin' or 'salesman'")

    # Prevent deactivating the last admin
    if user_data.is_active is not None and not user_data.is_active:
        # Count active admins
        admin_count = await db.execute(
            select(User).filter(
                User.role == UserRole.ADMIN.value,
                User.is_active == 1
            )
        )
        active_admins = len(admin_count.scalars().all())
        if user.role == UserRole.ADMIN.value and active_admins <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot deactivate the last admin user"
            )

    # Update fields
    if user_data.username is not None:
        user.username = user_data.username
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.password is not None:
        user.hashed_password = hash_password(user_data.password)
    if user_data.role is not None:
        user.role = user_data.role
    if user_data.is_active is not None:
        user.is_active = 1 if user_data.is_active else 0

    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.post("/{user_id}/suspend", response_model=UserResponse)
async def suspend_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """
    Suspend a user account.

    **Admin Only**: This endpoint requires Admin role.
    Returns 403 Forbidden if accessed by Salesman.

    Suspended users cannot login or place orders.
    Cannot suspend the last admin user.
    """
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent suspending the last admin
    if user.role == UserRole.ADMIN.value:
        admin_count = await db.execute(
            select(User).filter(
                User.role == UserRole.ADMIN.value,
                User.is_active == 1
            )
        )
        active_admins = len(admin_count.scalars().all())
        if active_admins <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot suspend the last admin user"
            )

    user.is_active = 0
    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """
    Activate a suspended user account.

    **Admin Only**: This endpoint requires Admin role.
    Returns 403 Forbidden if accessed by Salesman.
    """
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = 1
    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.post("/{user_id}/promote", response_model=UserResponse)
async def promote_to_admin(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """
    Promote a salesman to admin role.

    **Admin Only**: This endpoint requires Admin role.
    Returns 403 Forbidden if accessed by Salesman.
    """
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role == UserRole.ADMIN.value:
        raise HTTPException(status_code=400, detail="User is already an admin")

    user.role = UserRole.ADMIN.value
    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.post("/{user_id}/demote", response_model=UserResponse)
async def demote_to_salesman(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """
    Demote an admin to salesman role.

    **Admin Only**: This endpoint requires Admin role.
    Returns 403 Forbidden if accessed by Salesman.

    Cannot demote the last admin user.
    """
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=400, detail="User is not an admin")

    # Prevent demoting the last admin
    admin_count = await db.execute(
        select(User).filter(
            User.role == UserRole.ADMIN.value,
            User.is_active == 1
        )
    )
    active_admins = len(admin_count.scalars().all())
    if active_admins <= 1:
        raise HTTPException(
            status_code=400,
            detail="Cannot demote the last admin user"
        )

    user.role = UserRole.SALESMAN.value
    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)
