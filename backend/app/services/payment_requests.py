"""Custom-order payment requests (spec §F).

Admin creates a request → the server computes the total and creates an order in
PAYMENT_REQUESTED with a 32-byte token (hash stored). The buyer pays via the
public link (captured immediately), moving the order into ACCEPTED.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core import ids
from app.models import (
    Customer,
    DeliveryType,
    Order,
    OrderEvent,
    OrderItem,
    OrderStatus,
    Payment,
    PaymentRequest,
    PaymentRequestStatus,
    PaymentStatus,
)
from app.notifications.service import notify_order
from app.notifications.templates import NotificationKind
from app.payments import PaymentIntent, PaymentProvider
from app.schemas import CustomItem, PaymentRequestCreate, PaymentRequestUpdate


class PaymentRequestError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 422) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def _amount(items: list[CustomItem], discount_cents: int) -> tuple[int, int]:
    subtotal = sum(i.price_cents for i in items)
    return subtotal, max(subtotal - discount_cents, 0)


def effective_status(pr: PaymentRequest, now: datetime | None = None) -> str:
    now = now or datetime.now(UTC)
    expires = pr.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=UTC)
    terminal = {PaymentRequestStatus.PAID, PaymentRequestStatus.CANCELLED}
    if pr.status not in terminal and expires < now:
        return PaymentRequestStatus.EXPIRED.value
    return pr.status.value


async def get_by_token_hash(
    session: AsyncSession, token_hash: str
) -> PaymentRequest | None:
    return await session.scalar(
        select(PaymentRequest)
        .where(PaymentRequest.token_hash == token_hash)
        .options(
            selectinload(PaymentRequest.order).selectinload(Order.items),
            selectinload(PaymentRequest.order).selectinload(Order.customer),
            selectinload(PaymentRequest.order).selectinload(Order.recipient),
        )
    )


async def create(
    session: AsyncSession, data: PaymentRequestCreate
) -> tuple[PaymentRequest, str]:
    subtotal, amount = _amount(data.items, data.discount_cents)
    order = Order(
        status=OrderStatus.PAYMENT_REQUESTED,
        customer=Customer(
            name=data.customer,
            email=data.email,
            phone=data.whatsapp,
            locale=data.locale,
        ),
        delivery_type=DeliveryType.ROME_SAME_DAY,  # custom orders: arranged manually
        subtotal_cents=subtotal,
        total_cents=amount,
        card_message=data.card_message,
        hide_sender=data.hide_sender,
    )
    for item in data.items:
        order.items.append(
            OrderItem(
                name_snapshot=item.title,
                quantity=1,
                unit_price_cents=item.price_cents,
            )
        )
    session.add(order)
    await session.flush()
    order.number = ids.order_number(order.id, datetime.now(UTC).year)

    token = ids.new_token()
    pr = PaymentRequest(
        order=order,  # set the relationship so pr.order is loaded for serialisation
        token_hash=ids.hash_token(token),
        status=PaymentRequestStatus.SENT,
        customer=data.customer,
        email=data.email,
        whatsapp=data.whatsapp,
        recipient=data.recipient,
        delivery_slot=data.delivery_slot,
        card_message=data.card_message,
        items=[i.model_dump() for i in data.items],
        amount_cents=amount,
        discount_cents=data.discount_cents,
        hide_sender=data.hide_sender,
        locale=data.locale,
        expires_at=datetime.now(UTC) + timedelta(hours=data.expiry_hours),
    )
    session.add(pr)
    await session.commit()
    notify_order(
        order, NotificationKind.PAYMENT_REQUEST, link=f"{settings.pay_base_url}/{token}"
    )
    return pr, token


async def update(
    session: AsyncSession, pr: PaymentRequest, data: PaymentRequestUpdate
) -> str:
    """Edit before payment — regenerates the token (old link dies)."""
    if pr.status in (PaymentRequestStatus.PAID, PaymentRequestStatus.CANCELLED):
        raise PaymentRequestError(
            "not_editable", "A paid or cancelled request can't be edited.", 409
        )
    fields = data.model_dump(exclude_unset=True)
    items = data.items if data.items is not None else [
        CustomItem(**i) for i in pr.items
    ]
    for key, value in fields.items():
        if key == "items":
            pr.items = [i.model_dump() for i in data.items or []]
        else:
            setattr(pr, key, value)
    _subtotal, amount = _amount(items, pr.discount_cents)
    pr.amount_cents = amount
    pr.status = PaymentRequestStatus.SENT
    pr.last_viewed_at = None

    order = pr.order
    order.subtotal_cents = sum(i.price_cents for i in items)
    order.total_cents = amount
    for existing in list(order.items):
        await session.delete(existing)
    order.items = [
        OrderItem(name_snapshot=i.title, quantity=1, unit_price_cents=i.price_cents)
        for i in items
    ]

    token = ids.new_token()
    pr.token_hash = ids.hash_token(token)
    await session.commit()
    return token


async def cancel(session: AsyncSession, pr: PaymentRequest) -> None:
    if pr.status == PaymentRequestStatus.PAID:
        raise PaymentRequestError(
            "already_paid", "A paid request can't be cancelled.", 409
        )
    pr.status = PaymentRequestStatus.CANCELLED
    await session.commit()


async def resend(session: AsyncSession, pr: PaymentRequest) -> str:
    if pr.status in (PaymentRequestStatus.PAID, PaymentRequestStatus.CANCELLED):
        raise PaymentRequestError("not_resendable", "Nothing to resend.", 409)
    token = ids.new_token()
    pr.token_hash = ids.hash_token(token)
    pr.status = PaymentRequestStatus.SENT
    current_expiry = pr.expires_at
    if current_expiry.tzinfo is None:
        current_expiry = current_expiry.replace(tzinfo=UTC)
    pr.expires_at = max(current_expiry, datetime.now(UTC) + timedelta(hours=48))
    await session.commit()
    return token


async def duplicate(
    session: AsyncSession, pr: PaymentRequest
) -> tuple[PaymentRequest, str]:
    data = PaymentRequestCreate(
        customer=pr.customer,
        email=pr.email,
        whatsapp=pr.whatsapp,
        recipient=pr.recipient,
        delivery_slot=pr.delivery_slot,
        card_message=pr.card_message,
        items=[CustomItem(**i) for i in pr.items],
        discount_cents=pr.discount_cents,
        hide_sender=pr.hide_sender,
        locale=pr.locale,
    )
    return await create(session, data)


async def reissue_token(session: AsyncSession, pr: PaymentRequest) -> str:
    """Issue a fresh token for a (re)printed PDF. Any previously distributed link
    for this request stops working — intentional (only the hash is stored)."""
    token = ids.new_token()
    pr.token_hash = ids.hash_token(token)
    await session.commit()
    return token


async def record_view(session: AsyncSession, pr: PaymentRequest) -> None:
    if pr.status == PaymentRequestStatus.SENT:
        pr.status = PaymentRequestStatus.VIEWED
    pr.last_viewed_at = datetime.now(UTC)
    await session.commit()


async def pay(
    session: AsyncSession, provider: PaymentProvider, pr: PaymentRequest
) -> PaymentIntent:
    if effective_status(pr) == PaymentRequestStatus.EXPIRED.value:
        raise PaymentRequestError("expired", "This payment request has expired.", 410)
    if pr.status in (PaymentRequestStatus.PAID, PaymentRequestStatus.CANCELLED):
        raise PaymentRequestError("not_payable", "This request can't be paid.", 409)

    order = pr.order
    intent = provider.create_intent(
        amount_cents=pr.amount_cents,
        currency="EUR",
        manual_capture=False,  # custom orders capture immediately
        metadata={"order_id": str(order.id), "order_number": order.number},
    )
    session.add(
        Payment(
            order_id=order.id,
            stripe_payment_intent_id=intent.id,
            amount_cents=pr.amount_cents,
            status=PaymentStatus.CAPTURED,
        )
    )
    pr.status = PaymentRequestStatus.PAID
    prev = order.status
    order.status = OrderStatus.ACCEPTED
    session.add(
        OrderEvent(
            order_id=order.id,
            actor="system",
            from_status=prev,
            to_status=OrderStatus.ACCEPTED,
            note="payment request paid",
        )
    )
    await session.commit()
    notify_order(order, NotificationKind.PAYMENT_RECEIVED)
    return intent


async def verify(
    session: AsyncSession, order_number: str, email: str
) -> PaymentRequest | None:
    """Confirm a request is genuine. Both order number AND email must match —
    no partial matches, no enumeration."""
    return await session.scalar(
        select(PaymentRequest)
        .join(Order, PaymentRequest.order_id == Order.id)
        .where(
            Order.number == order_number,
            func.lower(PaymentRequest.email) == email.lower(),
        )
    )


async def list_requests(
    session: AsyncSession, status: PaymentRequestStatus | None = None
) -> list[PaymentRequest]:
    where = [PaymentRequest.status == status] if status else []
    result = await session.scalars(
        select(PaymentRequest)
        .where(*where)
        .order_by(PaymentRequest.id.desc())
        .options(selectinload(PaymentRequest.order))
    )
    return list(result.all())


async def get_with_order(
    session: AsyncSession, pr_id: int
) -> PaymentRequest | None:
    return await session.scalar(
        select(PaymentRequest)
        .where(PaymentRequest.id == pr_id)
        .options(selectinload(PaymentRequest.order).selectinload(Order.items))
    )
