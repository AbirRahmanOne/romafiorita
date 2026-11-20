from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.payments import PaymentProvider, get_payment_provider
from app.schemas import CheckoutRequest, CheckoutResponse
from app.services.checkout import CheckoutError, create_checkout

router = APIRouter(prefix="/v1", tags=["checkout"])


@router.post("/checkout", response_model=CheckoutResponse, operation_id="checkout")
async def checkout(
    data: CheckoutRequest,
    session: AsyncSession = Depends(get_session),
    provider: PaymentProvider = Depends(get_payment_provider),
) -> CheckoutResponse:
    try:
        order, token, intent = await create_checkout(session, provider, data)
    except CheckoutError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": exc.message},
        ) from exc
    return CheckoutResponse(
        order_number=order.number,
        token=token,
        client_secret=intent.client_secret,
        subtotal_cents=order.subtotal_cents,
        delivery_cents=order.delivery_fee_cents,
        time_fee_cents=order.time_fee_cents,
        total_cents=order.total_cents,
        currency=order.currency,
    )
