"""
Authentication and Authorization Dependencies for FastAPI.

This module provides:
- CurrentUser: Dataclass representing the authenticated user context
- get_current_user: Dependency to extract and validate user from auth token/header
- Role-based access control dependencies
- Order ownership verification utilities

Usage:
    from app.auth.dependencies import get_current_user, get_current_salesman_or_admin

    @router.get("/protected")
    async def protected_endpoint(current_user: CurrentUser = Depends(get_current_user)):
        return {"user_id": current_user.id, "role": current_user.role}
"""

from fastapi import Depends, HTTPException, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

from ..models import UserRole, User
from ..database import get_db


# Security scheme for Swagger UI
security_scheme = HTTPBearer(auto_error=False)


class UserContextError(Exception):
    """Custom exception for authentication/authorization errors."""
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


@dataclass
class CurrentUser:
    """
    Represents the authenticated user context extracted from the request.

    Attributes:
        id: Unique user identifier from the database
        username: User's username
        role: User's role (Admin/Salesman)
        is_active: Whether the user account is active
        token_type: Type of authentication used (bearer/token)
    """
    id: int
    username: str
    role: str
    is_active: bool = True
    token_type: str = "bearer"

    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == UserRole.ADMIN.value

    def is_salesman(self) -> bool:
        """Check if user has salesman role."""
        return self.role == UserRole.SALESMAN.value

    def can_access_order(self, order_user_id: int) -> bool:
        """
        Check if user can access an order.

        Admins can access all orders.
        Salesmen can only access their own orders.
        """
        return self.is_admin() or self.id == order_user_id

    def has_role(self, required_role: str) -> bool:
        """Check if user has a specific role."""
        return self.role == required_role

    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the specified roles."""
        return self.role in roles

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "is_active": self.is_active,
            "is_admin": self.is_admin(),
            "is_salesman": self.is_salesman(),
        }


def extract_user_id_from_token(token: str) -> Optional[int]:
    """
    Extract user ID from a token string.

    In production, this would decode a JWT token.
    For simulation, we extract from a simple format.

    Args:
        token: The authentication token

    Returns:
        User ID if valid, None otherwise
    """
    # Simulation: Token format "user_{id}_{role}"
    # In production: JWT.decode(token, SECRET_KEY, algorithms=["HS256"])
    try:
        if token.startswith("user_"):
            parts = token.split("_")
            if len(parts) >= 2:
                return int(parts[1])
    except (ValueError, IndexError):
        pass
    return None


def validate_simulated_headers(
    x_simulated_role: Optional[str],
    x_simulated_user_id: Optional[int],
    x_simulated_username: Optional[str]
) -> CurrentUser:
    """
    Validate simulated authentication headers and create CurrentUser.

    Headers:
        X-Simulated-Role: 'admin' or 'salesman' (required)
        X-Simulated-User-Id: User ID (optional, defaults based on role)
        X-Simulated-Username: Username (optional, defaults based on role)

    Returns:
        CurrentUser object with validated context

    Raises:
        HTTPException: If authentication fails
    """
    if x_simulated_role is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Set X-Simulated-Role header to 'admin' or 'salesman'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Determine role
    role = x_simulated_role.lower()
    if role not in [UserRole.ADMIN.value, UserRole.SALESMAN.value]:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid role '{x_simulated_role}'. Use 'admin' or 'salesman'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Set defaults based on role
    if role == UserRole.ADMIN.value:
        default_id = 1
        default_username = "admin"
    else:
        default_id = x_simulated_user_id if x_simulated_user_id else 2
        default_username = x_simulated_username or f"salesman_{default_id}"

    user_id = x_simulated_user_id if x_simulated_user_id else default_id
    username = x_simulated_username or default_username

    return CurrentUser(
        id=user_id,
        username=username,
        role=role,
        is_active=True,
        token_type="simulated"
    )


async def get_current_user_from_db(request: Request) -> Optional[CurrentUser]:
    """
    Attempt to load user from database based on session/token.

    This is called after header validation to enrich user context.
    In production, this would verify JWT and load user from database.

    Args:
        request: FastAPI request object

    Returns:
        CurrentUser if found in DB, None otherwise
    """
    # In production, implement JWT verification:
    # auth_header = request.headers.get("Authorization")
    # if auth_header and auth_header.startswith("Bearer "):
    #     token = auth_header.split(" ")[1]
    #     payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    #     user = await db.get_user_by_id(payload["sub"])
    #     return CurrentUser.from_db_model(user)

    # For simulation, return None to use header-based user
    return None


async def get_current_user(
    request: Request,
    x_simulated_role: Optional[str] = Header(None, alias="X-Simulated-Role"),
    x_simulated_user_id: Optional[int] = Header(None, alias="X-Simulated-User-Id"),
    x_simulated_username: Optional[str] = Header(None, alias="X-Simulated-Username"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> CurrentUser:
    """
    Extract and validate the current user from the request.

    This is the main authentication dependency. It supports:
    1. Simulated headers (X-Simulated-Role, X-Simulated-User-Id)
    2. Bearer token authentication (JWT in production)

    Args:
        request: FastAPI request object
        x_simulated_role: Role from simulated header
        x_simulated_user_id: User ID from simulated header
        x_simulated_username: Username from simulated header
        credentials: Bearer token credentials (for JWT)

    Returns:
        CurrentUser object with authenticated context

    Raises:
        HTTPException: If authentication fails

    Example:
        @router.get("/me")
        async def get_me(current_user: CurrentUser = Depends(get_current_user)):
            return current_user.to_dict()
    """
    # Try bearer token first (for production JWT)
    if credentials:
        user_id = extract_user_id_from_token(credentials.credentials)
        if user_id:
            # In production, load user from database
            # For simulation, create a basic user from token
            return CurrentUser(
                id=user_id,
                username=f"user_{user_id}",
                role=UserRole.SALESMAN.value,
                is_active=True,
                token_type="bearer"
            )

    # Fall back to simulated headers
    return validate_simulated_headers(
        x_simulated_role,
        x_simulated_user_id,
        x_simulated_username
    )


async def get_current_active_user(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CurrentUser:
    """
    Verify that the current user is active and not suspended.

    Queries the database to check the latest user status.
    This invalidates active sessions when a user is suspended.

    Args:
        request: FastAPI request object (for DB access)
        current_user: User from get_current_user dependency

    Returns:
        CurrentUser if active

    Raises:
        HTTPException: If user account is suspended

    Example:
        @router.get("/profile")
        async def get_profile(user: CurrentUser = Depends(get_current_active_user)):
            return {"profile": user.username}
    """
    # Check database for latest user status to invalidate sessions on suspension
    result = await db.execute(
        select(User).filter(User.id == current_user.id)
    )
    db_user = result.scalar_one_or_none()

    if db_user and db_user.is_active == 0:
        raise HTTPException(
            status_code=403,
            detail="Account is suspended"
        )

    return current_user


async def get_current_salesman(
    current_user: CurrentUser = Depends(get_current_active_user)
) -> CurrentUser:
    """
    Verify that the current user is an active salesman.

    Use this for endpoints that should only be accessible by salesmen.

    Args:
        current_user: User from get_current_active_user dependency

    Returns:
        CurrentUser if user is a salesman

    Raises:
        HTTPException: If user is not a salesman

    Example:
        @router.post("/orders")
        async def create_order(user: CurrentUser = Depends(get_current_salesman)):
            return {"created_by": user.id}
    """
    if not current_user.is_salesman():
        raise HTTPException(
            status_code=403,
            detail="Salesman role required. Admin access denied."
        )
    return current_user


async def get_current_admin(
    current_user: CurrentUser = Depends(get_current_active_user)
) -> CurrentUser:
    """
    Verify that the current user is an active admin.

    Use this for admin-only endpoints.

    Args:
        current_user: User from get_current_active_user dependency

    Returns:
        CurrentUser if user is an admin

    Raises:
        HTTPException: If user is not an admin

    Example:
        @router.get("/admin/users")
        async def list_users(admin: CurrentUser = Depends(get_current_admin)):
            return {"users": []}
    """
    if not current_user.is_admin():
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required."
        )
    return current_user


async def get_current_salesman_or_admin(
    current_user: CurrentUser = Depends(get_current_active_user)
) -> CurrentUser:
    """
    Verify that the current user is an active salesman or admin.

    This is the primary dependency for order endpoints and other
    shared functionality accessible by both roles.

    Args:
        current_user: User from get_current_active_user dependency

    Returns:
        CurrentUser if user is a salesman or admin

    Raises:
        HTTPException: If user has insufficient permissions

    Example:
        @router.post("/orders")
        async def create_order(user: CurrentUser = Depends(get_current_salesman_or_admin)):
            return {"created_by": user.id, "role": user.role}
    """
    if not current_user.is_salesman() and not current_user.is_admin():
        raise HTTPException(
            status_code=403,
            detail="Salesman or Admin role required."
        )
    return current_user


def require_order_ownership(order_user_id: int, current_user: CurrentUser) -> None:
    """
    Verify that the current user owns the order or is an admin.

    Call this in endpoints that need to verify order ownership.

    Args:
        order_user_id: ID of the user who created the order
        current_user: Current authenticated user

    Raises:
        HTTPException: If user doesn't own the order and isn't an admin

    Example:
        @router.get("/orders/{order_id}")
        async def get_order(
            order_id: int,
            user: CurrentUser = Depends(get_current_salesman_or_admin),
            db: AsyncSession = Depends(get_db)
        ):
            order = await get_order_from_db(order_id, db)
            require_order_ownership(order.user_id, user)
            return order
    """
    if not current_user.can_access_order(order_user_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied. You can only access your own orders."
        )


def require_roles(*roles: str):
    """
    Dependency factory for requiring specific roles.

    Args:
        *roles: Variable number of allowed roles

    Returns:
        Dependency function that validates user role

    Example:
        @router.get("/special")
        async def special_endpoint(
            user: CurrentUser = Depends(require_roles("admin", "manager"))
        ):
            return {"access": "granted"}
    """
    async def role_checker(current_user: CurrentUser = Depends(get_current_active_user)) -> CurrentUser:
        if not current_user.has_any_role(list(roles)):
            raise HTTPException(
                status_code=403,
                detail=f"Required roles: {', '.join(roles)}"
            )
        return current_user
    return role_checker
