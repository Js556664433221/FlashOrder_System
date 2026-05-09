from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..database import get_db
from ..models import Product
from ..schemas import ProductStockResponse
from ..auth.dependencies import get_current_active_user, CurrentUser

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/categories")
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    Get all unique product categories.
    """
    result = await db.execute(
        select(distinct(Product.category))
        .where(Product.category.isnot(None))
        .where(Product.category != "")
        .order_by(Product.category)
    )
    categories = [row[0] for row in result.all() if row[0]]
    return {"categories": categories}


@router.get("/", response_model=dict)
async def list_products(
    search: Optional[str] = Query(None, description="Search by SKU or name"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(9, ge=1, le=100, description="Number of products per page"),
    offset: int = Query(0, ge=0, description="Number of products to skip"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """
    List products with pagination and filtering support.

    Returns products in a paginated format with metadata:
    - products: List of products for current page
    - total: Total count of products matching filters
    - page: Current page number (1-indexed)
    - per_page: Number of products per page
    - total_pages: Total number of pages
    """
    # Base query
    query = select(Product)
    count_query = select(func.count()).select_from(Product)

    # Apply category filter
    if category:
        category_condition = Product.category == category
        query = query.filter(category_condition)
        count_query = count_query.filter(category_condition)

    # Apply search filter
    if search:
        search_filter = f"%{search}%"
        search_condition = or_(
            Product.sku.ilike(search_filter),
            Product.name.ilike(search_filter)
        )
        query = query.filter(search_condition)
        count_query = count_query.filter(search_condition)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.offset(offset).limit(limit)

    # Execute query
    result = await db.execute(query)
    products = result.scalars().all()

    # Calculate pagination info
    page = (offset // limit) + 1 if limit > 0 else 1
    total_pages = (total + limit - 1) // limit if limit > 0 else 1

    return {
        "products": [
            ProductStockResponse(
                id=p.id,
                sku=p.sku,
                name=p.name,
                physical_stock=p.physical_stock,
                reserved_stock=p.reserved_stock,
                available_stock=p.physical_stock - p.reserved_stock,
                price=p.price,
                description=p.description,
                category=p.category,
                image_url=p.image_url
            ) for p in products
        ],
        "total": total,
        "page": page,
        "per_page": limit,
        "total_pages": total_pages
    }


@router.get("/{product_id}", response_model=ProductStockResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    result = await db.execute(select(Product).filter(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductStockResponse(
        id=product.id,
        sku=product.sku,
        name=product.name,
        physical_stock=product.physical_stock,
        reserved_stock=product.reserved_stock,
        available_stock=product.physical_stock - product.reserved_stock,
        price=product.price,
        description=product.description,
        category=product.category,
        image_url=product.image_url
    )