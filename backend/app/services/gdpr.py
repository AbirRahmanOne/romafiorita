"""GDPR subject-access (export) and erasure (delete) for a customer.

Erasure strips personal data but keeps financial records (order totals/status)
for legal retention — it anonymises rather than hard-deletes orders.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Customer, Order, PaymentRequest


async def _find_customer(session: AsyncSession, email: str) -> Customer | None:
    return await session.scalar(
        select(Customer)
        .where(func.lower(Customer.email) == email.lower())
        .options(
            selectinload(Customer.recipients),
            selectinload(Customer.orders).selectinload(Order.items),
            selectinload(Customer.orders).selectinload(Order.events),
        )
    )


async def export_customer(session: AsyncSession, email: str) -> dict[str, Any] | None:
    customer = await _find_customer(session, email)
    if customer is None:
        return None
    requests = (
        await session.scalars(
            select(PaymentRequest).where(
                func.lower(PaymentRequest.email) == email.lower()
            )
        )
    ).all()
    return {
        "customer": {
            "id": customer.id,
            "email": customer.email,
            "name": customer.name,
            "phone": customer.phone,
            "country": customer.country,
            "locale": customer.locale,
        },
        "recipients": [
            {
                "name": r.name,
                "phone": r.phone,
                "address_line": r.address_line,
                "cap": r.cap,
                "city": r.city,
            }
            for r in customer.recipients
        ],
        "orders": [
            {
                "number": o.number,
                "status": o.status.value,
                "total_cents": o.total_cents,
                "card_message": o.card_message,
                "items": [
                    {"name": i.name_snapshot, "tier": i.tier_snapshot,
                     "quantity": i.quantity, "unit_price_cents": i.unit_price_cents}
                    for i in o.items
                ],
            }
            for o in customer.orders
        ],
        "payment_requests": [
            {"id": pr.id, "status": pr.status.value, "amount_cents": pr.amount_cents}
            for pr in requests
        ],
    }


async def delete_customer(session: AsyncSession, email: str) -> bool:
    """Right to erasure: anonymise the customer's PII. Returns False if unknown."""
    customer = await _find_customer(session, email)
    if customer is None:
        return False
    customer.email = None
    customer.name = "[deleted]"
    customer.phone = None
    customer.country = None
    for recipient in customer.recipients:
        recipient.name = "[deleted]"
        recipient.phone = None
        recipient.address_line = "[deleted]"
    for order in customer.orders:
        order.card_message = None
    await session.commit()
    return True
