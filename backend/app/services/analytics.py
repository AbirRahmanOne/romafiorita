"""Sales analytics + dashboard, computed from our own orders.

ponytail: aggregates in Python over fetched rows — fine at a flower shop's volume.
Move to SQL GROUP BY if the order table grows large.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.delivery import ROME_TZ
from app.models import Order, OrderStatus, Product

# Orders whose payment has been captured count as revenue.
PAID = {
    OrderStatus.ACCEPTED,
    OrderStatus.AWAITING_PHOTO,
    OrderStatus.PHOTO_SENT,
    OrderStatus.APPROVED,
    OrderStatus.OUT_FOR_DELIVERY,
    OrderStatus.DELIVERED,
}
AWAITING_PHOTO = {OrderStatus.ACCEPTED, OrderStatus.AWAITING_PHOTO}


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _rome_date(dt: datetime) -> date:
    return _aware(dt).astimezone(ROME_TZ).date()


def _on_time_pct(delivered: Sequence[Order]) -> float:
    rated = [o for o in delivered if o.delivery_date is not None]
    if not rated:
        return 100.0
    on_time = sum(
        1
        for o in rated
        if o.delivery_date is not None and _rome_date(o.updated_at) <= o.delivery_date
    )
    return round(on_time / len(rated) * 100, 1)


def _dash_order(o: Order) -> dict[str, Any]:
    return {
        "id": o.id,
        "number": o.number,
        "status": o.status.value,
        "recipient_name": o.recipient.name if o.recipient else None,
        "slot_start": o.slot_start,
        "total_cents": o.total_cents,
        "bouquet_photo": o.bouquet_photo,
    }


def _series(
    rev_by_day: dict[date, int], today: date, days: int
) -> list[dict[str, Any]]:
    return [
        {
            "day": (today - timedelta(days=i)).isoformat(),
            "revenue_cents": rev_by_day.get(today - timedelta(days=i), 0),
        }
        for i in range(days - 1, -1, -1)
    ]


async def compute_dashboard(session: AsyncSession) -> dict[str, Any]:
    now = datetime.now(UTC)
    today = now.astimezone(ROME_TZ).date()
    window_start = now - timedelta(days=7)
    start_of_today = datetime.combine(today, time.min, ROME_TZ).astimezone(UTC)

    recent = (
        await session.scalars(
            select(Order).where(
                Order.status.in_(PAID), Order.created_at >= window_start
            )
        )
    ).all()
    rev_by_day: dict[date, int] = defaultdict(int)
    revenue_today = 0
    for o in recent:
        d = _rome_date(o.created_at)
        rev_by_day[d] += o.total_cents
        if d == today:
            revenue_today += o.total_cents

    orders_today = await session.scalar(
        select(func.count())
        .select_from(Order)
        .where(Order.created_at >= start_of_today)
    )
    pending = (
        await session.scalars(
            select(Order)
            .where(Order.status.in_(AWAITING_PHOTO))
            .options(selectinload(Order.recipient))
        )
    ).all()
    schedule = (
        await session.scalars(
            select(Order)
            .where(Order.delivery_date == today)
            .order_by(Order.slot_start)
            .options(selectinload(Order.recipient))
        )
    ).all()
    delivered = (
        await session.scalars(
            select(Order).where(Order.status == OrderStatus.DELIVERED)
        )
    ).all()

    return {
        "kpis": {
            "revenue_today_cents": revenue_today,
            "orders_today": orders_today or 0,
            "on_time_pct": _on_time_pct(delivered),
            "photos_to_send": len(pending),
        },
        # Google Search Console not wired yet (ADR/Phase note).
        "google": {"clicks": 0, "delta_pct": 0.0, "orders_from_search": 0},
        "revenue_series": _series(rev_by_day, today, 7),
        "schedule": [_dash_order(o) for o in schedule],
        "pending_photos": [_dash_order(o) for o in pending],
    }


def _breakdown(agg: dict[str, list[int]]) -> list[dict[str, Any]]:
    return [
        {"key": key, "revenue_cents": rev, "orders": n}
        for key, (rev, n) in sorted(agg.items(), key=lambda kv: -kv[1][0])
    ]


async def compute_sales(session: AsyncSession, range_days: int) -> dict[str, Any]:
    now = datetime.now(UTC)
    today = now.astimezone(ROME_TZ).date()
    cutoff = now - timedelta(days=range_days)

    orders = (
        await session.scalars(
            select(Order)
            .where(Order.status.in_(PAID), Order.created_at >= cutoff)
            .options(selectinload(Order.items), selectinload(Order.customer))
        )
    ).all()
    occasion_by_product = dict(
        (await session.execute(select(Product.id, Product.occasion))).all()
    )

    rev_by_day: dict[date, int] = defaultdict(int)
    by_delivery: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    by_country: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    by_occasion: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    by_tier: dict[str, list[int]] = defaultdict(lambda: [0, 0])

    for o in orders:
        rev_by_day[_rome_date(o.created_at)] += o.total_cents
        by_delivery[o.delivery_type.value][0] += o.total_cents
        by_delivery[o.delivery_type.value][1] += 1
        country = (o.customer.country if o.customer else None) or "unknown"
        by_country[country][0] += o.total_cents
        by_country[country][1] += 1
        for item in o.items:
            line = item.unit_price_cents * item.quantity
            occ = (
                occasion_by_product.get(item.product_id)
                if item.product_id is not None
                else None
            ) or "unknown"
            by_occasion[occ][0] += line
            by_occasion[occ][1] += item.quantity
            tier = item.tier_snapshot or "unknown"
            by_tier[tier][0] += line
            by_tier[tier][1] += item.quantity

    counts = (
        await session.execute(
            select(Order.customer_id, func.count())
            .where(Order.status.in_(PAID), Order.customer_id.is_not(None))
            .group_by(Order.customer_id)
        )
    ).all()
    new_customers = sum(1 for _, c in counts if c == 1)
    repeat_customers = sum(1 for _, c in counts if c > 1)

    delivered = (
        await session.scalars(
            select(Order).where(Order.status == OrderStatus.DELIVERED)
        )
    ).all()

    return {
        "range_days": range_days,
        "revenue_series": _series(rev_by_day, today, range_days),
        "by_occasion": _breakdown(by_occasion),
        "by_tier": _breakdown(by_tier),
        "by_delivery_type": _breakdown(by_delivery),
        "by_country": _breakdown(by_country),
        "new_customers": new_customers,
        "repeat_customers": repeat_customers,
        "on_time_pct": _on_time_pct(delivered),
    }
