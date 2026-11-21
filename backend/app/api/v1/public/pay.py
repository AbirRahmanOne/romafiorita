from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import ids
from app.db import get_session
from app.deps import rate_limit
from app.payments import PaymentProvider, get_payment_provider
from app.schemas import (
    CustomItem,
    PayIntentResponse,
    PaySummary,
    VerifyRequest,
    VerifyResponse,
)
from app.services import payment_requests as svc

router = APIRouter(prefix="/v1", tags=["pay"])


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={"code": "pay_not_found", "message": "Payment request not found."},
    )


@router.get("/pay/{token}", response_model=PaySummary, operation_id="getPaySummary")
async def get_pay(
    token: str,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> PaySummary:
    pr = await svc.get_by_token_hash(session, ids.hash_token(token))
    if pr is None:
        raise _not_found()
    await svc.record_view(session, pr)
    response.headers["X-Robots-Tag"] = "noindex"
    return PaySummary(
        order_number=pr.order.number,
        items=[CustomItem(**i) for i in pr.items],
        recipient=pr.recipient,
        delivery_slot=pr.delivery_slot,
        card_message=pr.card_message,
        amount_cents=pr.amount_cents,
        currency=pr.currency,
        local_estimate=None,  # FX owned by backend; real rates land later
        status=svc.effective_status(pr),
        expires_at=pr.expires_at,
    )


@router.post(
    "/pay/{token}/intent",
    response_model=PayIntentResponse,
    operation_id="payIntent",
    dependencies=[Depends(rate_limit("pay", limit=10))],
)
async def pay_intent(
    token: str,
    session: AsyncSession = Depends(get_session),
    provider: PaymentProvider = Depends(get_payment_provider),
) -> PayIntentResponse:
    pr = await svc.get_by_token_hash(session, ids.hash_token(token))
    if pr is None:
        raise _not_found()
    try:
        intent = await svc.pay(session, provider, pr)
    except svc.PaymentRequestError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": exc.message},
        ) from exc
    return PayIntentResponse(
        client_secret=intent.client_secret, order_number=pr.order.number
    )


@router.post(
    "/verify",
    response_model=VerifyResponse,
    operation_id="verifyOrder",
    dependencies=[Depends(rate_limit("verify", limit=5))],
)
async def verify(
    body: VerifyRequest, session: AsyncSession = Depends(get_session)
) -> VerifyResponse:
    pr = await svc.verify(session, body.order_number, body.email)
    if pr is None:
        return VerifyResponse(genuine=False)
    return VerifyResponse(
        genuine=True,
        order_number=body.order_number,
        amount_cents=pr.amount_cents,
        status=svc.effective_status(pr),
    )
