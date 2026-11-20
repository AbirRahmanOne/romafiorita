from collections.abc import Sequence

from sqlalchemy import ColumnElement, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import AddOn, Product, ProductVariant


async def list_products(
    session: AsyncSession,
    *,
    occasion: str | None = None,
    category: str | None = None,
    include_inactive: bool = False,
) -> Sequence[Product]:
    where: list[ColumnElement[bool]] = []
    if not include_inactive:
        where.append(Product.is_active.is_(True))
    if occasion:
        where.append(Product.occasion == occasion)
    if category:
        where.append(Product.category == category)
    result = await session.scalars(
        select(Product)
        .where(*where)
        .order_by(Product.sort_order, Product.id)
        .options(selectinload(Product.variants))
    )
    return result.all()


async def get_product_by_slug(
    session: AsyncSession, slug: str, *, include_inactive: bool = False
) -> Product | None:
    where: list[ColumnElement[bool]] = [Product.slug == slug]
    if not include_inactive:
        where.append(Product.is_active.is_(True))
    return await session.scalar(
        select(Product).where(*where).options(selectinload(Product.variants))
    )


async def slug_exists(session: AsyncSession, slug: str) -> bool:
    return (
        await session.scalar(select(Product.id).where(Product.slug == slug))
    ) is not None


async def list_addons(session: AsyncSession) -> Sequence[AddOn]:
    result = await session.scalars(
        select(AddOn).where(AddOn.is_active.is_(True)).order_by(AddOn.id)
    )
    return result.all()


async def variant_prices_by_sku(
    session: AsyncSession, skus: Sequence[str]
) -> dict[str, int]:
    """Price per sku for buyable variants: both the variant and its product must
    be active. Missing/inactive/hidden skus are simply absent."""
    if not skus:
        return {}
    rows = await session.execute(
        select(ProductVariant.sku, ProductVariant.price_cents)
        .join(Product, ProductVariant.product_id == Product.id)
        .where(
            ProductVariant.sku.in_(skus),
            ProductVariant.is_active.is_(True),
            Product.is_active.is_(True),
        )
    )
    return {sku: price for sku, price in rows.all()}


async def addon_prices_by_code(
    session: AsyncSession, codes: Sequence[str]
) -> dict[str, int]:
    if not codes:
        return {}
    rows = await session.execute(
        select(AddOn.code, AddOn.price_cents).where(
            AddOn.code.in_(codes), AddOn.is_active.is_(True)
        )
    )
    return {code: price for code, price in rows.all()}
