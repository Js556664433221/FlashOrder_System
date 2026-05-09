from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import ForwardRef
import jwt
import hashlib

from ..database import get_db
from ..models import User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"

security = HTTPBearer()


class UserResponse(BaseModel):
    id: int
    username: str
    role: str

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    user: UserResponse
    token: str


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_token(user_id: int) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return JWT token."""
    result = await db.execute(select(User).filter(User.username == login_data.username))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    hashed_pw = hash_password(login_data.password)
    if user.hashed_password != hashed_pw:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is suspended")

    token = create_token(user.id)

    return LoginResponse(
        user=UserResponse(id=user.id, username=user.username, role=user.role),
        token=token
    )


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Verify JWT token and return user."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is suspended")

    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Get current user information from JWT token.

    This endpoint fetches the latest user data from the database,
    ensuring that role changes (e.g., promotions) are reflected
    immediately without requiring the user to re-login.

    Returns:
        Current user information including the latest role
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role
    )