from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import CustomerProfile
from ..auth.dependencies import get_current_salesman_or_admin, CurrentUser
from ..schemas import CustomerProfileCreate, CustomerProfileUpdate, CustomerProfileResponse

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/", response_model=list[CustomerProfileResponse])
async def list_customers(
    current_user: CurrentUser = Depends(get_current_salesman_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    List all customer profiles belonging to the current salesman.
    Each salesman can only see their own customer profiles.
    """
    result = await db.execute(
        select(CustomerProfile)
        .filter(CustomerProfile.salesman_id == current_user.id)
        .order_by(CustomerProfile.created_at.desc())
    )
    customers = result.scalars().all()
    return [
        CustomerProfileResponse(
            id=c.id,
            salesman_id=c.salesman_id,
            name=c.name,
            company_name=c.company_name,
            location=c.location,
            contact_number=c.contact_number,
            email=c.email,
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in customers
    ]


@router.post("/", response_model=CustomerProfileResponse, status_code=201)
async def create_customer(
    customer_data: CustomerProfileCreate,
    current_user: CurrentUser = Depends(get_current_salesman_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new customer profile.
    The customer profile is automatically associated with the current salesman.
    """
    customer = CustomerProfile(
        salesman_id=current_user.id,
        name=customer_data.name,
        company_name=customer_data.company_name,
        location=customer_data.location,
        contact_number=customer_data.contact_number,
        email=customer_data.email
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)

    return CustomerProfileResponse(
        id=customer.id,
        salesman_id=customer.salesman_id,
        name=customer.name,
        company_name=customer.company_name,
        location=customer.location,
        contact_number=customer.contact_number,
        email=customer.email,
        created_at=customer.created_at,
        updated_at=customer.updated_at
    )


@router.get("/{customer_id}", response_model=CustomerProfileResponse)
async def get_customer(
    customer_id: int,
    current_user: CurrentUser = Depends(get_current_salesman_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific customer profile.
    Salesmen can only view their own customer profiles.
    """
    result = await db.execute(
        select(CustomerProfile)
        .filter(
            CustomerProfile.id == customer_id,
            CustomerProfile.salesman_id == current_user.id
        )
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer profile not found")

    return CustomerProfileResponse(
        id=customer.id,
        salesman_id=customer.salesman_id,
        name=customer.name,
        company_name=customer.company_name,
        location=customer.location,
        contact_number=customer.contact_number,
        email=customer.email,
        created_at=customer.created_at,
        updated_at=customer.updated_at
    )


@router.patch("/{customer_id}", response_model=CustomerProfileResponse)
async def update_customer(
    customer_id: int,
    customer_data: CustomerProfileUpdate,
    current_user: CurrentUser = Depends(get_current_salesman_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a customer profile.
    Salesmen can only update their own customer profiles.
    """
    result = await db.execute(
        select(CustomerProfile)
        .filter(
            CustomerProfile.id == customer_id,
            CustomerProfile.salesman_id == current_user.id
        )
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer profile not found")

    if customer_data.name is not None:
        customer.name = customer_data.name
    if customer_data.company_name is not None:
        customer.company_name = customer_data.company_name
    if customer_data.location is not None:
        customer.location = customer_data.location
    if customer_data.contact_number is not None:
        customer.contact_number = customer_data.contact_number
    if customer_data.email is not None:
        customer.email = customer_data.email

    await db.commit()
    await db.refresh(customer)

    return CustomerProfileResponse(
        id=customer.id,
        salesman_id=customer.salesman_id,
        name=customer.name,
        company_name=customer.company_name,
        location=customer.location,
        contact_number=customer.contact_number,
        email=customer.email,
        created_at=customer.created_at,
        updated_at=customer.updated_at
    )


@router.delete("/{customer_id}", status_code=204)
async def delete_customer(
    customer_id: int,
    current_user: CurrentUser = Depends(get_current_salesman_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a customer profile.
    Salesmen can only delete their own customer profiles.
    """
    result = await db.execute(
        select(CustomerProfile)
        .filter(
            CustomerProfile.id == customer_id,
            CustomerProfile.salesman_id == current_user.id
        )
    )
    customer = result.scalar_one_or_none()

    if not customer:
        raise HTTPException(status_code=404, detail="Customer profile not found")

    await db.delete(customer)
    await db.commit()
