from collections.abc import Sequence

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product


async def list_products(
    session: AsyncSession,
    *,
    occasion: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[Sequence[Product], int]:
    where: list[ColumnElement[bool]] = [Product.is_active.is_(True)]
    if occasion:
        where.append(Product.occasion == occasion)

    items = (
        await session.scalars(
            select(Product).where(*where).order_by(Product.id).limit(limit).offset(offset)
        )
    ).all()
    total = await session.scalar(
        select(func.count()).select_from(Product).where(*where)
    )
    return items, total or 0


async def get_product_by_slug(
    session: AsyncSession, slug: str
) -> Product | None:
    return await session.scalar(
        select(Product).where(
            Product.slug == slug, Product.is_active.is_(True)
        )
    )
