"""Race-safe slot booking.

The booking decision is a single atomic UPDATE guarded by ``held_count <
capacity``. The database serialises row updates, so two concurrent checkouts can
never push ``held_count`` past ``capacity`` — no overbooking, no app-level lock.

ponytail: expired HELD reservations are not reclaimed here; a release/sweep job
(Phase 5) decrements ``held_count``. Until then a lapsed hold keeps its seat.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import cast

from sqlalchemy import CursorResult, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import SlotCapacity


async def _ensure_counter(
    session: AsyncSession, slot_date: date, slot_start: datetime, capacity: int
) -> None:
    exists = await session.scalar(
        select(SlotCapacity.id).where(
            SlotCapacity.slot_date == slot_date,
            SlotCapacity.slot_start == slot_start,
        )
    )
    if exists is not None:
        return
    try:
        async with session.begin_nested():  # savepoint: survive a concurrent insert
            session.add(
                SlotCapacity(
                    slot_date=slot_date,
                    slot_start=slot_start,
                    capacity=capacity,
                    held_count=0,
                )
            )
    except IntegrityError:
        pass  # created concurrently — fine, the UPDATE below will handle it


async def book_slot(
    session: AsyncSession, slot_date: date, slot_start: datetime, capacity: int
) -> bool:
    """Atomically take one seat. Returns False if the slot is full."""
    await _ensure_counter(session, slot_date, slot_start, capacity)
    result = cast(
        "CursorResult[object]",
        await session.execute(
            update(SlotCapacity)
            .where(
                SlotCapacity.slot_date == slot_date,
                SlotCapacity.slot_start == slot_start,
                SlotCapacity.held_count < SlotCapacity.capacity,
            )
            .values(held_count=SlotCapacity.held_count + 1)
        ),
    )
    return result.rowcount == 1


async def release_slot(
    session: AsyncSession, slot_date: date, slot_start: datetime
) -> None:
    await session.execute(
        update(SlotCapacity)
        .where(
            SlotCapacity.slot_date == slot_date,
            SlotCapacity.slot_start == slot_start,
            SlotCapacity.held_count > 0,
        )
        .values(held_count=SlotCapacity.held_count - 1)
    )


async def full_slot_starts(session: AsyncSession, slot_date: date) -> set[datetime]:
    """Slot starts that are at capacity on ``slot_date`` (for availability)."""
    rows = await session.execute(
        select(SlotCapacity.slot_start).where(
            SlotCapacity.slot_date == slot_date,
            SlotCapacity.held_count >= SlotCapacity.capacity,
        )
    )
    return {start for (start,) in rows.all()}
