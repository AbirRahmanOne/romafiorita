from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import csrf_protect, get_current_staff
from app.domain.orders import PaymentEffect, TransitionError, resolve
from app.models import Order, OrderEvent, OrderStatus, Payment, PaymentStatus, Staff
from app.notifications.service import notify_order
from app.notifications.templates import NotificationKind
from app.payments import PaymentProvider, get_payment_provider
from app.repositories import orders as repo
from app.repositories import slots as slot_repo
from app.schemas import (
    AdminOrderItem,
    AdminOrderListResponse,
    AdminOrderRead,
    OrderEventRead,
    PhotoBody,
    RefundBody,
)

router = APIRouter(prefix="/v1/admin/orders", tags=["admin-orders"])

_csrf = Depends(csrf_protect)

# TransitionError.code -> HTTP status.
_STATUS = {
    "forbidden": 403,
    "invalid_state": 409,
    "photo_required": 422,
    "unknown_action": 404,
}

# URL action (dashes) -> state-machine action.
_ACTIONS = {
    "accept": "accept",
    "decline": "decline",
    "send-photo": "send_photo",
    "approve": "approve",
    "dispatch": "dispatch",
    "deliver": "deliver",
}

# state-machine action -> buyer notification (actions not listed send nothing).
_NOTIFY = {
    "accept": NotificationKind.ACCEPTED,
    "decline": NotificationKind.DECLINED,
    "send_photo": NotificationKind.PHOTO_SENT,
    "dispatch": NotificationKind.OUT_FOR_DELIVERY,
    "deliver": NotificationKind.DELIVERED,
    "refund": NotificationKind.REFUNDED,
}


def _serialize(order: Order) -> AdminOrderRead:
    c, r = order.customer, order.recipient
    return AdminOrderRead(
        id=order.id,
        number=order.number,
        status=order.status.value,
        sender_name=c.name if c else None,
        sender_email=c.email if c else None,
        sender_country=c.country if c else None,
        recipient_name=r.name if r else None,
        recipient_address=r.address_line if r else None,
        recipient_cap=r.cap if r else None,
        delivery_type=order.delivery_type.value,
        delivery_date=order.delivery_date,
        slot_start=order.slot_start,
        total_cents=order.total_cents,
        currency=order.currency,
        card_message=order.card_message,
        hide_sender=order.hide_sender,
        bouquet_photo=order.bouquet_photo,
        items=[
            AdminOrderItem(
                name=i.name_snapshot,
                tier=i.tier_snapshot,
                quantity=i.quantity,
                unit_price_cents=i.unit_price_cents,
            )
            for i in order.items
        ],
        events=[
            OrderEventRead(
                actor=e.actor,
                from_status=e.from_status.value if e.from_status else None,
                to_status=e.to_status.value if e.to_status else None,
                note=e.note,
            )
            for e in order.events
        ],
    )


async def _get_or_404(session: AsyncSession, order_id: int) -> Order:
    order = await repo.get_by_id(session, order_id)
    if order is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "order_not_found", "message": "Order not found."},
        )
    return order


async def _run_effect(
    session: AsyncSession,
    provider: PaymentProvider,
    order: Order,
    effect: PaymentEffect,
    refund_cents: int | None = None,
) -> None:
    if effect is PaymentEffect.NONE:
        return
    payment = await session.scalar(
        select(Payment).where(Payment.order_id == order.id)
    )
    intent_id = payment.stripe_payment_intent_id if payment else None
    if intent_id is None:
        return
    if effect is PaymentEffect.CAPTURE:
        provider.capture(intent_id)
        if payment:
            payment.status = PaymentStatus.CAPTURED
    elif effect is PaymentEffect.CANCEL:
        provider.cancel(intent_id)
        if payment:
            payment.status = PaymentStatus.CANCELLED
        await _release_slot(session, order)
    elif effect is PaymentEffect.REFUND:
        provider.refund(intent_id, amount_cents=refund_cents)
        if payment:
            payment.status = (
                PaymentStatus.PARTIALLY_REFUNDED
                if refund_cents and refund_cents < payment.amount_cents
                else PaymentStatus.REFUNDED
            )


async def _release_slot(session: AsyncSession, order: Order) -> None:
    if order.slot_start and order.delivery_date:
        await slot_repo.release_slot(session, order.delivery_date, order.slot_start)


async def _transition(
    session: AsyncSession,
    provider: PaymentProvider,
    order: Order,
    action: str,
    staff: Staff,
    refund_cents: int | None = None,
) -> None:
    try:
        resolved = resolve(
            action,
            current=order.status,
            role=staff.role,
            has_photo=bool(order.bouquet_photo),
        )
    except TransitionError as exc:
        raise HTTPException(
            status_code=_STATUS.get(exc.code, 400),
            detail={"code": exc.code, "message": exc.message},
        ) from exc
    await _run_effect(session, provider, order, resolved.effect, refund_cents)
    prev = order.status
    order.status = resolved.target
    order.events.append(
        OrderEvent(
            actor=staff.email, from_status=prev, to_status=resolved.target, note=action
        )
    )
    await session.commit()
    kind = _NOTIFY.get(action)
    if kind is not None:
        notify_order(order, kind)


@router.get("", response_model=AdminOrderListResponse)
async def list_orders(
    status: str | None = None,
    q: str | None = None,
    session: AsyncSession = Depends(get_session),
    staff: Staff = Depends(get_current_staff),
) -> AdminOrderListResponse:
    status_enum = None
    if status:
        try:
            status_enum = OrderStatus(status)
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "invalid_status",
                    "message": f"Unknown status {status}",
                },
            ) from exc
    orders = await repo.list_orders(session, status=status_enum, query=q)
    counts = await repo.status_counts(session)
    return AdminOrderListResponse(
        items=[_serialize(o) for o in orders], counts=counts
    )


@router.get("/{order_id}", response_model=AdminOrderRead)
async def get_order(
    order_id: int,
    session: AsyncSession = Depends(get_session),
    staff: Staff = Depends(get_current_staff),
) -> AdminOrderRead:
    return _serialize(await _get_or_404(session, order_id))


@router.post("/{order_id}/photo", response_model=AdminOrderRead, dependencies=[_csrf])
async def upload_photo(
    order_id: int,
    body: PhotoBody,
    session: AsyncSession = Depends(get_session),
    provider: PaymentProvider = Depends(get_payment_provider),
    staff: Staff = Depends(get_current_staff),
) -> AdminOrderRead:
    order = await _get_or_404(session, order_id)
    order.bouquet_photo = body.url
    await _transition(session, provider, order, "photo", staff)
    return _serialize(order)


@router.post("/{order_id}/refund", response_model=AdminOrderRead, dependencies=[_csrf])
async def refund_order(
    order_id: int,
    body: RefundBody,
    session: AsyncSession = Depends(get_session),
    provider: PaymentProvider = Depends(get_payment_provider),
    staff: Staff = Depends(get_current_staff),
) -> AdminOrderRead:
    order = await _get_or_404(session, order_id)
    await _transition(session, provider, order, "refund", staff, body.amount_cents)
    return _serialize(order)


@router.post(
    "/{order_id}/{action}", response_model=AdminOrderRead, dependencies=[_csrf]
)
async def transition_order(
    order_id: int,
    action: str,
    session: AsyncSession = Depends(get_session),
    provider: PaymentProvider = Depends(get_payment_provider),
    staff: Staff = Depends(get_current_staff),
) -> AdminOrderRead:
    mapped = _ACTIONS.get(action)
    if mapped is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "unknown_action", "message": f"Unknown action {action}"},
        )
    order = await _get_or_404(session, order_id)
    await _transition(session, provider, order, mapped, staff)
    return _serialize(order)
