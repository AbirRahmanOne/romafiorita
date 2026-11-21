"""Background task functions (pure callables on a session).

Phase 5b schedules these with arq + Redis cron. They are written so they can be
unit-tested directly and called from a scheduler without change.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.delivery import RESERVATION_HOLD
from app.models import Order, OrderEvent, OrderStatus, Reminder
from app.notifications.service import notify_occasion_reminder
from app.repositories import slots as slot_repo

# Occasion reminders fire this many days before the date (spec §G).
REMINDER_LEAD_DAYS = (7, 2)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


async def expire_stale_holds(
    session: AsyncSession, now: datetime | None = None
) -> int:
    """Release slot holds for orders stuck in PENDING_PAYMENT past the hold window
    (unpaid checkouts), and mark them EXPIRED."""
    now = now or datetime.now(UTC)
    threshold = now - RESERVATION_HOLD
    orders = (
        await session.scalars(
            select(Order).where(Order.status == OrderStatus.PENDING_PAYMENT)
        )
    ).all()
    expired = 0
    for order in orders:
        if _aware(order.created_at) >= threshold:
            continue
        if order.slot_start and order.delivery_date:
            await slot_repo.release_slot(session, order.delivery_date, order.slot_start)
        order.status = OrderStatus.EXPIRED
        session.add(
            OrderEvent(
                order_id=order.id,
                actor="system",
                from_status=OrderStatus.PENDING_PAYMENT,
                to_status=OrderStatus.EXPIRED,
                note="reservation expired",
            )
        )
        expired += 1
    if expired:
        await session.commit()
    return expired


async def send_due_occasion_reminders(
    session: AsyncSession, today: date | None = None
) -> int:
    """Send occasion reminders due today (7 and 2 days before), once each."""
    today = today or datetime.now(UTC).date()
    target_dates = [today + timedelta(days=d) for d in REMINDER_LEAD_DAYS]
    reminders = (
        await session.scalars(
            select(Reminder)
            .where(Reminder.remind_on.in_(target_dates), Reminder.sent_at.is_(None))
            .options(selectinload(Reminder.customer))
        )
    ).all()
    sent = 0
    for reminder in reminders:
        customer = reminder.customer
        if customer and customer.email:
            notify_occasion_reminder(
                customer.email, customer.locale, reminder.occasion
            )
        reminder.sent_at = datetime.now(UTC)
        sent += 1
    if sent:
        await session.commit()
    return sent


async def anonymise_old_recipients(
    session: AsyncSession, cutoff: datetime
) -> int:
    """GDPR retention: strip recipient address/phone and card messages from
    delivered orders older than ``cutoff``."""
    orders = (
        await session.scalars(
            select(Order)
            .where(Order.status == OrderStatus.DELIVERED)
            .options(selectinload(Order.recipient))
        )
    ).all()
    anonymised = 0
    for order in orders:
        if _aware(order.updated_at) >= cutoff:
            continue
        if order.card_message is None and order.recipient is None:
            continue
        order.card_message = None
        if order.recipient:
            order.recipient.address_line = "[anonymised]"
            order.recipient.phone = None
        anonymised += 1
    if anonymised:
        await session.commit()
    return anonymised
