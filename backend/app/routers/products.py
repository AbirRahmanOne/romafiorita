from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.repositories import products as repo
from app.schemas import ProductList, ProductRead

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductList)
async def list_products(
    occasion: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> ProductList:
    items, total = await repo.list_products(
        session, occasion=occasion, limit=limit, offset=offset
    )
    return ProductList(
        items=[ProductRead.model_validate(p) for p in items], total=total
    )


@router.get("/{slug}", response_model=ProductRead)
async def get_product(
    slug: str, session: AsyncSession = Depends(get_session)
) -> ProductRead:
    product = await repo.get_product_by_slug(session, slug)
    if product is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "product_not_found",
                "message": "Product not found.",
            },
        )
    return ProductRead.model_validate(product)
