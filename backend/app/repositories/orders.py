from collections.abc import Sequence

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Customer, Order, OrderStatus, Recipient

_EAGER = (
    selectinload(Order.items),
    selectinload(Order.events),
    selectinload(Order.customer),
    selectinload(Order.recipient),
)


async def get_by_id(session: AsyncSession, order_id: int) -> Order | None:
    return await session.scalar(
        select(Order).where(Order.id == order_id).options(*_EAGER)
    )


async def get_by_token_hash(session: AsyncSession, token_hash: str) -> Order | None:
    return await session.scalar(
        select(Order).where(Order.track_token_hash == token_hash).options(*_EAGER)
    )


async def list_orders(
    session: AsyncSession,
    *,
    status: OrderStatus | None = None,
    query: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[Order]:
    where: list[ColumnElement[bool]] = []
    if status is not None:
        where.append(Order.status == status)
    if query:
        like = f"%{query}%"
        where.append(
            or_(
                Order.number.ilike(like),
                Order.customer.has(Customer.email.ilike(like)),
                Order.recipient.has(Recipient.name.ilike(like)),
            )
        )
    result = await session.scalars(
        select(Order)
        .where(*where)
        .order_by(Order.id.desc())
        .limit(limit)
        .offset(offset)
        .options(*_EAGER)
    )
    return result.all()


async def status_counts(session: AsyncSession) -> dict[str, int]:
    rows = await session.execute(
        select(Order.status, func.count()).group_by(Order.status)
    )
    return {status.value: count for status, count in rows.all()}
