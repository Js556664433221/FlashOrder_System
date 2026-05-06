from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ..database import get_db
from ..models import Product
from ..schemas import ProductStockResponse

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=list[ProductStockResponse])
async def list_products(
    search: Optional[str] = Query(None, description="Search by SKU or name"),
    db: AsyncSession = Depends(get_db)
):
    query = select(Product)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(Product.sku.ilike(search_filter), Product.name.ilike(search_filter))
        )
    result = await db.execute(query)
    products = result.scalars().all()
    return [ProductStockResponse(
        id=p.id,
        sku=p.sku,
        name=p.name,
        physical_stock=p.physical_stock,
        reserved_stock=p.reserved_stock,
        available_stock=p.physical_stock - p.reserved_stock,
        price=p.price,
        description=p.description
    ) for p in products]


@router.get("/{product_id}", response_model=ProductStockResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
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
        description=product.description
    )
