from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import slots as repo

# Slot datetimes are timezone-aware everywhere (checkout parses ISO with tz);
# Postgres stores timestamptz and returns aware UTC, so compare aware here too.
_SLOT = datetime(2026, 6, 15, 10, 0, tzinfo=UTC)
_DAY = _SLOT.date()
_START = _SLOT


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
    assert len(full) == 1
    # SQLite returns naive, Postgres aware — compare tz-agnostically.
    start = next(iter(full)).replace(tzinfo=None)
    assert start == _START.replace(tzinfo=None)
