"""
Promo Code Management Router.
Admin-only CRUD endpoints for managing promotional codes.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import Optional, List
from datetime import datetime

from ..database import get_db
from ..models import PromoCode, Order
from ..schemas import PromoCodeCreate, PromoCodeUpdate, PromoCodeResponse, DiscountType, PromoStatsResponse
from ..auth.dependencies import get_current_admin, CurrentUser

router = APIRouter(prefix="/admin/promo", tags=["promo"])


# NOTE: /stats must be before /{promo_id} to avoid being caught as an ID

@router.get("/", response_model=List[PromoCodeResponse])
async def list_promo_codes(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin),
    include_inactive: bool = Query(default=False)
):
    """List all promo codes. Admin only."""
    query = select(PromoCode).order_by(desc(PromoCode.created_at))
    if not include_inactive:
        query = query.filter(PromoCode.is_active == 1)
    result = await db.execute(query)
    promos = result.scalars().all()
    return [PromoCodeResponse.model_validate(p) for p in promos]


@router.get("/stats", response_model=List[PromoStatsResponse])
async def get_promo_stats(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """Get promo code statistics. Admin only."""
    result = await db.execute(
        select(
            PromoCode.id,
            PromoCode.code,
            PromoCode.discount_type,
            PromoCode.value,
            PromoCode.expiry_date,
            PromoCode.is_active,
            PromoCode.created_at,
            func.count(Order.id).label("usage_count"),
            func.coalesce(func.sum(Order.discount_amount), 0).label("total_discount_given")
        )
        .outerjoin(Order, Order.applied_promo_id == PromoCode.id)
        .group_by(PromoCode.id)
        .order_by(desc(PromoCode.created_at))
    )
    rows = result.all()
    return [
        PromoStatsResponse(
            id=row.id,
            code=row.code,
            discount_type=row.discount_type,
            value=float(row.value),
            expiry_date=row.expiry_date,
            is_active=bool(row.is_active),
            usage_count=row.usage_count,
            total_discount_given=float(row.total_discount_given),
            created_at=row.created_at
        )
        for row in rows
    ]


@router.get("/{promo_id}", response_model=PromoCodeResponse)
async def get_promo_code(
    promo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """Get a specific promo code by ID. Admin only."""
    result = await db.execute(select(PromoCode).filter(PromoCode.id == promo_id))
    promo = result.scalar_one_or_none()
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found")
    return PromoCodeResponse.model_validate(promo)


@router.post("/", response_model=PromoCodeResponse, status_code=201)
async def create_promo_code(
    promo_data: PromoCodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """Create a new promo code. Admin only."""
    result = await db.execute(select(PromoCode).filter(PromoCode.code == promo_data.code))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Promo code '{promo_data.code}' already exists")

    promo = PromoCode(
        code=promo_data.code.upper(),
        discount_type=promo_data.discount_type.value,
        value=promo_data.value,
        expiry_date=promo_data.expiry_date,
        is_active=1 if promo_data.is_active else 0,
        created_at=datetime.utcnow()
    )
    db.add(promo)
    await db.commit()
    await db.refresh(promo)
    return PromoCodeResponse.model_validate(promo)


@router.patch("/{promo_id}", response_model=PromoCodeResponse)
async def update_promo_code(
    promo_id: int,
    promo_data: PromoCodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """Update a promo code. Admin only."""
    result = await db.execute(select(PromoCode).filter(PromoCode.id == promo_id))
    promo = result.scalar_one_or_none()
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found")

    if promo_data.code is not None:
        promo.code = promo_data.code.upper()
    if promo_data.discount_type is not None:
        promo.discount_type = promo_data.discount_type.value
    if promo_data.value is not None:
        promo.value = promo_data.value
    if promo_data.expiry_date is not None:
        promo.expiry_date = promo_data.expiry_date
    if promo_data.is_active is not None:
        promo.is_active = 1 if promo_data.is_active else 0

    await db.commit()
    await db.refresh(promo)
    return PromoCodeResponse.model_validate(promo)


@router.delete("/{promo_id}", status_code=204)
async def delete_promo_code(
    promo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """Delete a promo code. Admin only."""
    result = await db.execute(select(PromoCode).filter(PromoCode.id == promo_id))
    promo = result.scalar_one_or_none()
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found")
    await db.delete(promo)
    await db.commit()


@router.post("/{promo_id}/activate", response_model=PromoCodeResponse)
async def activate_promo_code(
    promo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """Activate a promo code. Admin only."""
    result = await db.execute(select(PromoCode).filter(PromoCode.id == promo_id))
    promo = result.scalar_one_or_none()
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found")
    promo.is_active = 1
    await db.commit()
    await db.refresh(promo)
    return PromoCodeResponse.model_validate(promo)


@router.post("/{promo_id}/deactivate", response_model=PromoCodeResponse)
async def deactivate_promo_code(
    promo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_admin)
):
    """Deactivate a promo code. Admin only."""
    result = await db.execute(select(PromoCode).filter(PromoCode.id == promo_id))
    promo = result.scalar_one_or_none()
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found")
    promo.is_active = 0
    await db.commit()
    await db.refresh(promo)
    return PromoCodeResponse.model_validate(promo)
