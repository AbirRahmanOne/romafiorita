"""Admin payments views.

Built from our own `Payment` rows. Stripe-only data — balance-transaction fees,
payouts, balance, disputes — is null/empty until the real StripeProvider lands
(ADR 0002); those endpoints are deliberate stubs.
"""

from __future__ import annotations

import csv
import datetime
import io

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import require_roles
from app.models import Order, Payment, PaymentRequest, PaymentStatus, StaffRole
from app.schemas import (
    Balance,
    DisputesResponse,
    HeldListResponse,
    HeldPayment,
    MonthlyReport,
    PaymentKpis,
    PaymentRow,
    PaymentsListResponse,
    PayoutsResponse,
)

router = APIRouter(prefix="/v1/admin/payments", tags=["admin-payments"])

_can = Depends(require_roles(StaffRole.OWNER, StaffRole.MANAGER))

_PUBLIC_STATUS = {
    PaymentStatus.PENDING: "pending",
    PaymentStatus.AUTHORIZED: "held",
    PaymentStatus.CAPTURED: "captured",
    PaymentStatus.FAILED: "failed",
    PaymentStatus.CANCELLED: "cancelled",
    PaymentStatus.REFUNDED: "refunded",
    PaymentStatus.PARTIALLY_REFUNDED: "refunded",
}
_CAPTURED = {
    PaymentStatus.CAPTURED,
    PaymentStatus.REFUNDED,
    PaymentStatus.PARTIALLY_REFUNDED,
}
# Card holds last ~7 days (spec §4D); placeholder until per-method logic.
_HOLD = datetime.timedelta(days=7)


async def _rows(session: AsyncSession) -> list[tuple[Payment, str]]:
    result = await session.execute(
        select(Payment, Order.number)
        .join(Order, Payment.order_id == Order.id)
        .order_by(Payment.id.desc())
    )
    return list(result.all())


async def _request_order_ids(session: AsyncSession) -> set[int]:
    rows = await session.scalars(select(PaymentRequest.order_id))
    return set(rows.all())


@router.get("", response_model=PaymentsListResponse, dependencies=[_can])
async def list_payments(
    source: str | None = Query(default=None),
    status: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
) -> PaymentsListResponse:
    request_orders = await _request_order_ids(session)
    items: list[PaymentRow] = []
    gross = refunds = 0
    for payment, number in await _rows(session):
        src = "PAYMENT_REQUEST" if payment.order_id in request_orders else "WEBSITE"
        public = _PUBLIC_STATUS[payment.status]
        if payment.status in _CAPTURED:
            gross += payment.amount_cents
        if payment.status == PaymentStatus.REFUNDED:
            refunds += payment.amount_cents
        if (source and src != source) or (status and public != status):
            continue
        items.append(
            PaymentRow(
                id=payment.id,
                order_number=number,
                source=src,
                status=public,
                amount_cents=payment.amount_cents,
                currency=payment.currency,
                fee_cents=None,  # Stripe balance transaction — not available yet
                net_cents=None,
                created_at=payment.created_at,
            )
        )
    kpis = PaymentKpis(
        gross_cents=gross,
        fees_cents=0,
        refunds_cents=refunds,
        net_cents=gross - refunds,
    )
    return PaymentsListResponse(kpis=kpis, items=items)


@router.get("/held", response_model=HeldListResponse, dependencies=[_can])
async def held_payments(
    session: AsyncSession = Depends(get_session),
) -> HeldListResponse:
    items = []
    for payment, number in await _rows(session):
        if payment.status is not PaymentStatus.AUTHORIZED:
            continue
        created = payment.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=datetime.UTC)
        items.append(
            HeldPayment(
                id=payment.id,
                order_number=number,
                amount_cents=payment.amount_cents,
                currency=payment.currency,
                created_at=payment.created_at,
                hold_expires_at=created + _HOLD,
            )
        )
    return HeldListResponse(items=items)


@router.get("/reports/monthly", response_model=MonthlyReport, dependencies=[_can])
async def monthly_report(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    session: AsyncSession = Depends(get_session),
) -> MonthlyReport:
    today = datetime.date.today()
    month = month or f"{today.year:04d}-{today.month:02d}"
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["order_number", "date", "amount_eur", "status"])
    for payment, number in await _rows(session):
        created = payment.created_at
        if created.strftime("%Y-%m") != month:
            continue
        if payment.status not in _CAPTURED:
            continue
        writer.writerow(
            [
                number,
                created.date().isoformat(),
                f"{payment.amount_cents / 100:.2f}",
                _PUBLIC_STATUS[payment.status],
            ]
        )
    return MonthlyReport(
        month=month, filename=f"roma-fiorita-{month}.csv", csv=buf.getvalue()
    )


# Payouts / balance / disputes are Stripe-only reads — empty until StripeProvider
# lands (ADR 0002). Sibling paths under /v1/admin.
extras_router = APIRouter(prefix="/v1/admin", tags=["admin-payments"])


@extras_router.get("/payouts", response_model=PayoutsResponse, dependencies=[_can])
async def payouts() -> PayoutsResponse:
    return PayoutsResponse(
        items=[], balance=Balance(available_cents=0, pending_cents=0)
    )


@extras_router.get("/disputes", response_model=DisputesResponse, dependencies=[_can])
async def disputes() -> DisputesResponse:
    return DisputesResponse(items=[])
