"""
Public Promo Code Validation Router.

Endpoints for validating and applying promo codes during checkout.
These endpoints are accessible to all authenticated users.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import datetime, timezone

from ..database import get_db
from ..models import PromoCode
from ..schemas import PromoCodeValidationResult
from ..auth.dependencies import get_current_salesman_or_admin, CurrentUser

router = APIRouter(prefix="/promo", tags=["promo"])


class ValidatePromoRequest(BaseModel):
    code: str
    cart_total: float


@router.post("/validate", response_model=PromoCodeValidationResult)
async def validate_promo_code(
    request: ValidatePromoRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_salesman_or_admin)
):
    """
    Validate a promo code and calculate the discount.

    Checks:
    - Code exists
    - Code is active
    - Code has not expired

    Returns:
    - valid: Whether the code is valid
    - discount_type: "percentage" or "flat"
    - discount_value: The discount amount
    - message: Status message
    """
    # Find the promo code
    result = await db.execute(
        select(PromoCode).filter(PromoCode.code == request.code.upper())
    )
    promo = result.scalar_one_or_none()

    if not promo:
        return PromoCodeValidationResult(
            valid=False,
            message="Invalid promo code"
        )

    # Check if active
    if promo.is_active != 1:
        return PromoCodeValidationResult(
            valid=False,
            code=promo.code,
            message="This promo code is no longer active"
        )

    # Check expiry date
    if promo.expiry_date:
        now = datetime.now(timezone.utc)
        if promo.expiry_date.replace(tzinfo=timezone.utc) < now:
            return PromoCodeValidationResult(
                valid=False,
                code=promo.code,
                message="This promo code has expired"
            )

    # Calculate discount
    if promo.discount_type == "percentage":
        discount_amount = round(request.cart_total * (promo.value / 100), 2)
    else:  # flat
        discount_amount = min(promo.value, request.cart_total)

    return PromoCodeValidationResult(
        valid=True,
        code=promo.code,
        discount_type=promo.discount_type,
        discount_value=discount_amount,
        message="Promo code applied successfully"
    )
