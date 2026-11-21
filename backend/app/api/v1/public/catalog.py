from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.http_cache import cache_or_304
from app.db import get_session
from app.models import Product, ProductVariant
from app.repositories import catalog as repo
from app.schemas import (
    AddonListResponse,
    AddonRead,
    OccasionListResponse,
    OccasionRead,
    ProductListResponse,
    ProductRead,
    VariantRead,
)

router = APIRouter(prefix="/v1/catalog", tags=["catalog"])

Locale = Literal["it", "en"]

# Static occasion list (slug + localised names). Moves to content settings later.
OCCASIONS: list[OccasionRead] = [
    OccasionRead(
        slug="love", name_it="Amore e anniversario", name_en="Love & anniversary"
    ),
    OccasionRead(slug="birthday", name_it="Compleanno", name_en="Birthday"),
    OccasionRead(slug="thanks", name_it="Grazie", name_en="Thank you"),
    OccasionRead(slug="sympathy", name_it="Cordoglio", name_en="Sympathy"),
    OccasionRead(slug="baby", name_it="Nuovo arrivo", name_en="New baby"),
    OccasionRead(slug="getwell", name_it="Pronta guarigione", name_en="Get well"),
]


def _loc(it: str | None, en: str | None, locale: str) -> str:
    primary, fallback = (it, en) if locale == "it" else (en, it)
    return primary or fallback or ""


def serialize_variant(v: ProductVariant) -> VariantRead:
    return VariantRead(
        id=v.sku,
        tier=v.tier,
        price_cents=v.price_cents,
        description_it=v.description_it,
        description_en=v.description_en,
        images=v.images or [],
        active=v.is_active,
        is_default=v.is_default,
        same_day=v.same_day,
        exact_time=v.exact_time,
    )


def serialize_product(p: Product, locale: str) -> ProductRead:
    return ProductRead(
        slug=p.slug,
        name=_loc(p.name_it, p.name_en, locale),
        subtitle=_loc(p.subtitle_it, p.subtitle_en, locale) or None,
        occasion=p.occasion,
        category=p.category,
        tags=p.tags or [],
        images=p.images or [],
        variants=[serialize_variant(v) for v in p.variants if v.is_active],
    )


@router.get(
    "/products", response_model=ProductListResponse, operation_id="listProducts"
)
async def list_products(
    request: Request,
    response: Response,
    occasion: str | None = Query(default=None),
    category: str | None = Query(default=None),
    locale: Locale = Query(default="it"),
    session: AsyncSession = Depends(get_session),
) -> ProductListResponse | Response:
    products = await repo.list_products(session, occasion=occasion, category=category)
    result = ProductListResponse(
        items=[serialize_product(p, locale) for p in products]
    )
    return cache_or_304(request, response, result) or result


@router.get(
    "/products/{slug}", response_model=ProductRead, operation_id="getProduct"
)
async def get_product(
    slug: str,
    request: Request,
    response: Response,
    locale: Locale = Query(default="it"),
    session: AsyncSession = Depends(get_session),
) -> ProductRead | Response:
    product = await repo.get_product_by_slug(session, slug)
    if product is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "product_not_found", "message": "Product not found."},
        )
    result = serialize_product(product, locale)
    return cache_or_304(request, response, result) or result


@router.get(
    "/occasions", response_model=OccasionListResponse, operation_id="listOccasions"
)
async def list_occasions() -> OccasionListResponse:
    return OccasionListResponse(items=OCCASIONS)


@router.get("/addons", response_model=AddonListResponse, operation_id="listAddons")
async def list_addons(
    session: AsyncSession = Depends(get_session),
) -> AddonListResponse:
    addons = await repo.list_addons(session)
    return AddonListResponse(
        items=[
            AddonRead(
                id=a.code,
                name_it=a.name_it,
                name_en=a.name_en,
                price_cents=a.price_cents,
            )
            for a in addons
        ]
    )
