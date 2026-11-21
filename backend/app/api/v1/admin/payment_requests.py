from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_session
from app.deps import csrf_protect, require_roles
from app.models import PaymentRequest, PaymentRequestStatus, StaffRole
from app.schemas import (
    CustomItem,
    PaymentRequestCreate,
    PaymentRequestListResponse,
    PaymentRequestRead,
    PaymentRequestUpdate,
)
from app.services import payment_requests as svc
from app.services.pdf import generate_payment_request_pdf

router = APIRouter(
    prefix="/v1/admin/payment-requests", tags=["admin-payment-requests"]
)

_can = Depends(require_roles(StaffRole.OWNER, StaffRole.MANAGER))
_csrf = Depends(csrf_protect)


def _serialize(pr: PaymentRequest, token: str | None = None) -> PaymentRequestRead:
    return PaymentRequestRead(
        id=pr.id,
        order_number=pr.order.number,
        customer=pr.customer,
        email=pr.email,
        whatsapp=pr.whatsapp,
        amount_cents=pr.amount_cents,
        currency=pr.currency,
        status=svc.effective_status(pr),
        token=token,
        expires_at=pr.expires_at,
        last_viewed_at=pr.last_viewed_at,
        items=[CustomItem(**i) for i in pr.items],
        recipient=pr.recipient,
        delivery_slot=pr.delivery_slot,
        card_message=pr.card_message,
        discount_cents=pr.discount_cents,
        hide_sender=pr.hide_sender,
    )


async def _get_or_404(session: AsyncSession, pr_id: int) -> PaymentRequest:
    pr = await svc.get_with_order(session, pr_id)
    if pr is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Payment request not found."},
        )
    return pr


def _error(exc: svc.PaymentRequestError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code, "message": exc.message},
    )


@router.post(
    "", response_model=PaymentRequestRead, status_code=201, dependencies=[_can, _csrf]
)
async def create(
    data: PaymentRequestCreate, session: AsyncSession = Depends(get_session)
) -> PaymentRequestRead:
    pr, token = await svc.create(session, data)
    return _serialize(pr, token=token)


@router.get("", response_model=PaymentRequestListResponse, dependencies=[_can])
async def list_requests(
    status: str | None = None, session: AsyncSession = Depends(get_session)
) -> PaymentRequestListResponse:
    status_enum = None
    if status:
        try:
            status_enum = PaymentRequestStatus(status.upper())
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail={"code": "invalid_status", "message": f"Unknown {status}"},
            ) from exc
    rows = await svc.list_requests(session, status_enum)
    return PaymentRequestListResponse(items=[_serialize(pr) for pr in rows])


@router.patch(
    "/{pr_id}", response_model=PaymentRequestRead, dependencies=[_can, _csrf]
)
async def update(
    pr_id: int,
    data: PaymentRequestUpdate,
    session: AsyncSession = Depends(get_session),
) -> PaymentRequestRead:
    pr = await _get_or_404(session, pr_id)
    try:
        token = await svc.update(session, pr, data)
    except svc.PaymentRequestError as exc:
        raise _error(exc) from exc
    return _serialize(pr, token=token)


@router.post(
    "/{pr_id}/cancel", response_model=PaymentRequestRead, dependencies=[_can, _csrf]
)
async def cancel(
    pr_id: int, session: AsyncSession = Depends(get_session)
) -> PaymentRequestRead:
    pr = await _get_or_404(session, pr_id)
    try:
        await svc.cancel(session, pr)
    except svc.PaymentRequestError as exc:
        raise _error(exc) from exc
    return _serialize(pr)


@router.post(
    "/{pr_id}/resend", response_model=PaymentRequestRead, dependencies=[_can, _csrf]
)
async def resend(
    pr_id: int, session: AsyncSession = Depends(get_session)
) -> PaymentRequestRead:
    pr = await _get_or_404(session, pr_id)
    try:
        token = await svc.resend(session, pr)
    except svc.PaymentRequestError as exc:
        raise _error(exc) from exc
    return _serialize(pr, token=token)


@router.post(
    "/{pr_id}/duplicate",
    response_model=PaymentRequestRead,
    status_code=201,
    dependencies=[_can, _csrf],
)
async def duplicate(
    pr_id: int, session: AsyncSession = Depends(get_session)
) -> PaymentRequestRead:
    pr = await _get_or_404(session, pr_id)
    new_pr, token = await svc.duplicate(session, pr)
    return _serialize(new_pr, token=token)


@router.get("/{pr_id}/pdf", dependencies=[_can])
async def pdf(
    pr_id: int, session: AsyncSession = Depends(get_session)
) -> Response:
    pr = await _get_or_404(session, pr_id)
    if pr.status in (PaymentRequestStatus.PAID, PaymentRequestStatus.CANCELLED):
        raise HTTPException(
            status_code=409,
            detail={"code": "not_printable", "message": "Request is closed."},
        )
    # Reissuing a fresh link for the printout (prior links stop working).
    token = await svc.reissue_token(session, pr)
    content = generate_payment_request_pdf(
        pr, order_number=pr.order.number, pay_url=f"{settings.pay_base_url}/{token}"
    )
    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{pr.order.number}.pdf"'
        },
    )
