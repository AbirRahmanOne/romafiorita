from collections.abc import Sequence

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product
from app.schemas import ProductCreate, ProductUpdate


async def list_products(
    session: AsyncSession,
    *,
    occasion: str | None = None,
    include_inactive: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> tuple[Sequence[Product], int]:
    where: list[ColumnElement[bool]] = []
    if not include_inactive:
        where.append(Product.is_active.is_(True))
    if occasion:
        where.append(Product.occasion == occasion)

    items = (
        await session.scalars(
            select(Product)
            .where(*where)
            .order_by(Product.id)
            .limit(limit)
            .offset(offset)
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


async def get_product_by_id(
    session: AsyncSession, product_id: int
) -> Product | None:
    return await session.get(Product, product_id)


async def slug_exists(session: AsyncSession, slug: str) -> bool:
    count = await session.scalar(
        select(func.count()).select_from(Product).where(Product.slug == slug)
    )
    return (count or 0) > 0


async def create_product(
    session: AsyncSession, data: ProductCreate
) -> Product:
    product = Product(**data.model_dump())
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product


async def update_product(
    session: AsyncSession, product: Product, data: ProductUpdate
) -> Product:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    await session.commit()
    await session.refresh(product)
    return product


async def delete_product(session: AsyncSession, product: Product) -> None:
    await session.delete(product)
    await session.commit()
