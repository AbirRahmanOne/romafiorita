from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import slots as repo

_DAY = datetime(2026, 6, 15, 10, 0).date()
_START = datetime(2026, 6, 15, 10, 0)


async def test_capacity_cannot_be_exceeded(db_session: AsyncSession) -> None:
    # capacity 2: two bookings succeed, the third is refused.
    assert await repo.book_slot(db_session, _DAY, _START, capacity=2) is True
    assert await repo.book_slot(db_session, _DAY, _START, capacity=2) is True
    assert await repo.book_slot(db_session, _DAY, _START, capacity=2) is False


async def test_release_frees_a_seat(db_session: AsyncSession) -> None:
    assert await repo.book_slot(db_session, _DAY, _START, capacity=1) is True
    assert await repo.book_slot(db_session, _DAY, _START, capacity=1) is False
    await repo.release_slot(db_session, _DAY, _START)
    assert await repo.book_slot(db_session, _DAY, _START, capacity=1) is True


async def test_full_slot_starts(db_session: AsyncSession) -> None:
    await repo.book_slot(db_session, _DAY, _START, capacity=1)
    full = await repo.full_slot_starts(db_session, _DAY)
    assert _START in full
