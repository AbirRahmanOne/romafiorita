"""Checkout use case: validate → price → book slot → create order → authorise.

All prices are recomputed server-side. Website orders use manual capture: the
payment is authorised here (mock) and captured when the shop accepts the order.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import ids
from app.domain import delivery
from app.domain.pricing import Quote, QuoteLine, compute_quote
from app.models import (
    Customer,
    DeliveryType,
    Order,
    OrderEvent,
    OrderItem,
    OrderStatus,
    Payment,
    PaymentStatus,
    ProductVariant,
    Recipient,
)
from app.notifications.service import notify_order
from app.notifications.templates import NotificationKind
from app.payments import PaymentIntent, PaymentProvider
from app.repositories import catalog as catalog_repo
from app.repositories import slots as slot_repo
from app.schemas import CheckoutRequest

_DELIVERY_TYPE = {
    "standard": DeliveryType.ROME_SAME_DAY,
    "window": DeliveryType.ROME_WINDOW,
    "exact": DeliveryType.ROME_EXACT,
    "courier": DeliveryType.NATIONAL_COURIER,
}
_ROME_TYPES = {"standard", "window", "exact"}
_SLOTTED_TYPES = {"window", "exact"}


class CheckoutError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 422) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


async def create_checkout(
    session: AsyncSession, provider: PaymentProvider, data: CheckoutRequest
) -> tuple[Order, str, PaymentIntent]:
    zone = delivery.zone_for(data.recipient.cap)
    if zone is None:
        raise CheckoutError("invalid_postcode", "Not a valid Italian CAP.")

    dtype = data.delivery_type
    is_rome_type = dtype in _ROME_TYPES
    if (zone is delivery.Zone.ROME) != is_rome_type:
        raise CheckoutError(
            "invalid_delivery_type", f"{dtype} not available for zone {zone.value}."
        )

    # Resolve prices + snapshots server-side.
    variants = await catalog_repo.active_variants_by_sku(
        session, [i.variant_id for i in data.items]
    )
    codes = {c for item in data.items for c in item.addons}
    addon_prices = await catalog_repo.addon_prices_by_code(session, list(codes))

    lines: list[QuoteLine] = []
    for item in data.items:
        variant = variants.get(item.variant_id)
        if variant is None:
            raise CheckoutError("unknown_variant", f"Unknown variant {item.variant_id}")
        missing = [c for c in item.addons if c not in addon_prices]
        if missing:
            raise CheckoutError("unknown_addon", f"Unknown add-on(s): {missing}")
        lines.append(
            QuoteLine(
                unit_price_cents=variant.price_cents,
                quantity=item.quantity,
                addon_prices_cents=[addon_prices[c] for c in item.addons],
            )
        )
    quote = compute_quote(lines, dtype)

    # Book a slot for timed Rome deliveries (race-safe).
    slot_start: datetime | None = None
    slot_end: datetime | None = None
    delivery_date = datetime.now(delivery.ROME_TZ).date()
    if dtype in _SLOTTED_TYPES:
        if not data.delivery_slot:
            raise CheckoutError("slot_required", f"{dtype} needs a delivery slot.")
        slot_start = _parse_slot(data.delivery_slot)
        slot_end = slot_start + delivery.SLOT_STEP
        delivery_date = slot_start.astimezone(delivery.ROME_TZ).date()
        booked = await slot_repo.book_slot(
            session, delivery_date, slot_start, delivery.SLOT_CAPACITY
        )
        if not booked:
            raise CheckoutError("slot_unavailable", "That slot is full.", 409)

    order = _build_order(data, quote, _DELIVERY_TYPE[dtype], delivery_date, slot_start,
                         slot_end, variants)
    session.add(order)
    await session.flush()  # assign order.id

    order.number = ids.order_number(order.id, datetime.now(UTC).year)
    token = ids.new_token()
    order.track_token_hash = ids.hash_token(token)

    intent = provider.create_intent(
        amount_cents=quote.total_cents,
        currency="EUR",
        manual_capture=True,
        metadata={"order_id": str(order.id), "order_number": order.number},
    )
    session.add(
        Payment(
            order_id=order.id,
            stripe_payment_intent_id=intent.id,
            amount_cents=quote.total_cents,
            status=PaymentStatus.AUTHORIZED,
        )
    )

    # Mock: the hold is authorised immediately -> NEW. Real Stripe does this via
    # the payment_intent.amount_capturable_updated webhook.
    order.status = OrderStatus.NEW
    # Add by order_id, not order.events.append (the fresh collection isn't loaded).
    session.add(
        OrderEvent(
            order_id=order.id,
            actor="system",
            from_status=OrderStatus.PENDING_PAYMENT,
            to_status=OrderStatus.NEW,
            note="payment authorised",
        )
    )
    await session.commit()
    await notify_order(order, NotificationKind.ORDER_RECEIVED)
    return order, token, intent


def _parse_slot(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CheckoutError("invalid_slot", "delivery_slot must be ISO-8601.") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=delivery.ROME_TZ)
    return dt


def _build_order(
    data: CheckoutRequest,
    quote: Quote,
    dtype: DeliveryType,
    delivery_date: date,
    slot_start: datetime | None,
    slot_end: datetime | None,
    variants: dict[str, ProductVariant],
) -> Order:
    order = Order(
        status=OrderStatus.PENDING_PAYMENT,
        customer=Customer(
            name=data.sender.name,
            email=data.sender.email,
            phone=data.sender.phone,
            country=data.sender.country,
            locale=data.sender.locale,
        ),
        recipient=Recipient(
            name=data.recipient.name,
            phone=data.recipient.phone,
            address_line=data.recipient.address_line,
            cap=data.recipient.cap,
            city=data.recipient.city,
            address_type=data.recipient.address_type,
        ),
        delivery_type=dtype,
        delivery_date=delivery_date,
        slot_start=slot_start,
        slot_end=slot_end,
        subtotal_cents=quote.subtotal_cents,
        delivery_fee_cents=quote.delivery_cents,
        time_fee_cents=quote.time_fee_cents,
        total_cents=quote.total_cents,
        currency=quote.currency,
        card_message=data.card_message,
        hide_sender=data.hide_sender,
    )
    for item in data.items:
        variant = variants[item.variant_id]
        product = variant.product
        order.items.append(
            OrderItem(
                product_id=product.id,
                variant_id=variant.id,
                name_snapshot=product.name_en or product.name_it,
                tier_snapshot=variant.tier.value,
                quantity=item.quantity,
                unit_price_cents=variant.price_cents,
            )
        )
    return order
