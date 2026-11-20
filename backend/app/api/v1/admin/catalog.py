from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.public.catalog import serialize_product
from app.db import get_session
from app.deps import csrf_protect, require_roles
from app.models import Product, ProductVariant, StaffRole
from app.repositories import catalog as repo
from app.schemas import ProductCreate, ProductRead

router = APIRouter(prefix="/v1/admin/products", tags=["admin-catalog"])

# Catalog writes: OWNER/MANAGER only, CSRF-protected (cookie auth).
_can_write = Depends(require_roles(StaffRole.OWNER, StaffRole.MANAGER))
_csrf = Depends(csrf_protect)


def _validate_variants(data: ProductCreate) -> None:
    tiers = [v.tier for v in data.variants]
    if len(set(tiers)) != len(tiers):
        raise HTTPException(
            status_code=422,
            detail={"code": "duplicate_tier", "message": "Each tier may appear once."},
        )
    if sum(1 for v in data.variants if v.is_default) != 1:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "one_default_required",
                "message": "Exactly one variant must be the default.",
            },
        )


@router.post(
    "", response_model=ProductRead, status_code=201, dependencies=[_can_write, _csrf]
)
async def create_product(
    data: ProductCreate, session: AsyncSession = Depends(get_session)
) -> ProductRead:
    _validate_variants(data)
    if await repo.slug_exists(session, data.slug):
        raise HTTPException(
            status_code=409,
            detail={"code": "slug_taken", "message": "Slug already exists."},
        )
    product = Product(
        slug=data.slug,
        name_it=data.name_it,
        name_en=data.name_en,
        subtitle_it=data.subtitle_it,
        subtitle_en=data.subtitle_en,
        occasion=data.occasion,
        category=data.category,
        tags=data.tags,
        images=data.images,
        is_active=data.is_active,
    )
    for v in data.variants:
        product.variants.append(
            ProductVariant(
                sku=f"{data.slug}-{v.tier.value.lower()}",
                tier=v.tier,
                price_cents=v.price_cents,
                description_it=v.description_it,
                description_en=v.description_en,
                images=v.images,
                is_default=v.is_default,
                same_day=v.same_day,
                exact_time=v.exact_time,
                stock=v.stock,
            )
        )
    session.add(product)
    await session.commit()
    return serialize_product(product, "it")
