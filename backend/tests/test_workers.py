from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Customer,
    DeliveryType,
    Order,
    OrderStatus,
    Recipient,
    Reminder,
)
from app.repositories import slots as slot_repo
from app.workers import tasks

_DAY = datetime(2027, 6, 15, 10, 0).date()
_SLOT = datetime(2027, 6, 15, 10, 0, tzinfo=UTC)


async def test_expire_stale_holds_releases_slot(db_session: AsyncSession) -> None:
    assert await slot_repo.book_slot(db_session, _DAY, _SLOT, capacity=1) is True
    old = datetime.now(UTC) - timedelta(hours=1)
    order = Order(
        status=OrderStatus.PENDING_PAYMENT,
        delivery_type=DeliveryType.ROME_EXACT,
        delivery_date=_DAY,
        slot_start=_SLOT,
        total_cents=4900,
        created_at=old,
    )
    db_session.add(order)
    await db_session.commit()

    assert await tasks.expire_stale_holds(db_session) == 1
    await db_session.refresh(order)
    assert order.status is OrderStatus.EXPIRED
    # Seat freed -> bookable again.
    assert await slot_repo.book_slot(db_session, _DAY, _SLOT, capacity=1) is True


async def test_recent_hold_is_not_expired(db_session: AsyncSession) -> None:
    order = Order(
        status=OrderStatus.PENDING_PAYMENT,
        delivery_type=DeliveryType.ROME_EXACT,
        total_cents=4900,
        created_at=datetime.now(UTC),
    )
    db_session.add(order)
    await db_session.commit()
    assert await tasks.expire_stale_holds(db_session) == 0


async def test_due_occasion_reminders(db_session: AsyncSession, emails: Any) -> None:
    today = datetime.now(UTC).date()
    customer = Customer(email="buyer@example.com", name="Buyer", locale="en")
    db_session.add(customer)
    await db_session.flush()
    db_session.add_all(
        [
            Reminder(customer_id=customer.id, occasion="birthday",
                     remind_on=today + timedelta(days=7)),
            Reminder(customer_id=customer.id, occasion="anniversary",
                     remind_on=today + timedelta(days=30)),  # not due
        ]
    )
    await db_session.commit()

    assert await tasks.send_due_occasion_reminders(db_session, today) == 1
    assert emails.sent[-1].template == "occasion_reminder.v1"
    # Idempotent: already-sent reminder isn't sent again.
    assert await tasks.send_due_occasion_reminders(db_session, today) == 0


async def test_anonymise_old_recipients(db_session: AsyncSession) -> None:
    old = datetime.now(UTC) - timedelta(days=400)
    order = Order(
        status=OrderStatus.DELIVERED,
        delivery_type=DeliveryType.ROME_SAME_DAY,
        total_cents=4900,
        card_message="Secret message",
        recipient=Recipient(
            name="Rita", address_line="Via Appia 1", cap="00144", city="Roma"
        ),
        created_at=old,
        updated_at=old,
    )
    db_session.add(order)
    await db_session.commit()

    cutoff = datetime.now(UTC) - timedelta(days=180)
    assert await tasks.anonymise_old_recipients(db_session, cutoff) == 1
    # expire_on_commit=False: assert on the in-memory objects (no lazy reload).
    assert order.card_message is None
    assert order.recipient.address_line == "[anonymised]"
