from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import csrf_protect, require_roles
from app.models import StaffRole
from app.repositories import products as repo
from app.schemas import ProductCreate, ProductList, ProductRead, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])

# Catalog writes are OWNER/MANAGER only and CSRF-protected (cookie auth).
_can_write = Depends(require_roles(StaffRole.OWNER, StaffRole.MANAGER))
_csrf = Depends(csrf_protect)


@router.get("", response_model=ProductList)
async def list_products(
    occasion: str | None = Query(default=None),
    include_inactive: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> ProductList:
    items, total = await repo.list_products(
        session,
        occasion=occasion,
        include_inactive=include_inactive,
        limit=limit,
        offset=offset,
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
            detail={"code": "product_not_found", "message": "Product not found."},
        )
    return ProductRead.model_validate(product)


@router.post(
    "", response_model=ProductRead, status_code=201, dependencies=[_can_write, _csrf]
)
async def create_product(
    data: ProductCreate, session: AsyncSession = Depends(get_session)
) -> ProductRead:
    if await repo.slug_exists(session, data.slug):
        raise HTTPException(
            status_code=409,
            detail={
                "code": "slug_taken",
                "message": "A product with this slug already exists.",
            },
        )
    product = await repo.create_product(session, data)
    return ProductRead.model_validate(product)


@router.patch(
    "/id/{product_id}", response_model=ProductRead, dependencies=[_can_write, _csrf]
)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    session: AsyncSession = Depends(get_session),
) -> ProductRead:
    product = await repo.get_product_by_id(session, product_id)
    if product is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "product_not_found", "message": "Product not found."},
        )
    product = await repo.update_product(session, product, data)
    return ProductRead.model_validate(product)


@router.delete(
    "/id/{product_id}", status_code=204, dependencies=[_can_write, _csrf]
)
async def delete_product(
    product_id: int, session: AsyncSession = Depends(get_session)
) -> Response:
    product = await repo.get_product_by_id(session, product_id)
    if product is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "product_not_found", "message": "Product not found."},
        )
    await repo.delete_product(session, product)
    return Response(status_code=204)
