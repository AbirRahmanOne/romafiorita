"""Pricing — pure business logic. Totals are always computed here from
server-resolved prices; the client only ever sends IDs (spec §4C).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.delivery import TIME_FEE_CENTS


@dataclass(frozen=True)
class QuoteLine:
    unit_price_cents: int
    quantity: int
    addon_prices_cents: Sequence[int] = ()


@dataclass(frozen=True)
class Quote:
    subtotal_cents: int
    delivery_cents: int
    time_fee_cents: int
    total_cents: int
    currency: str = "EUR"


def compute_quote(lines: Sequence[QuoteLine], delivery_type: str = "standard") -> Quote:
    """variant + add-ons per line, × quantity, + time fee. Delivery is all-in (0)."""
    subtotal = sum(
        (line.unit_price_cents + sum(line.addon_prices_cents)) * line.quantity
        for line in lines
    )
    time_fee = TIME_FEE_CENTS.get(delivery_type, 0)
    return Quote(
        subtotal_cents=subtotal,
        delivery_cents=0,
        time_fee_cents=time_fee,
        total_cents=subtotal + time_fee,
    )
