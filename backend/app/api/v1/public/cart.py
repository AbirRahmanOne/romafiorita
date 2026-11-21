from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.domain.pricing import QuoteLine, compute_quote
from app.repositories import catalog as repo
from app.schemas import CartQuoteRequest, CartQuoteResponse

router = APIRouter(prefix="/v1/cart", tags=["cart"])


@router.post("/quote", response_model=CartQuoteResponse, operation_id="quoteCart")
async def quote(
    body: CartQuoteRequest, session: AsyncSession = Depends(get_session)
) -> CartQuoteResponse:
    # Resolve every id server-side — the client never sends prices (spec §4C).
    variant_prices = await repo.variant_prices_by_sku(
        session, [i.variant_id for i in body.items]
    )
    addon_codes = {code for item in body.items for code in item.addons}
    addon_prices = await repo.addon_prices_by_code(session, list(addon_codes))

    lines: list[QuoteLine] = []
    for item in body.items:
        if item.variant_id not in variant_prices:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "unknown_variant",
                    "message": f"Unknown or inactive variant: {item.variant_id}",
                },
            )
        missing = [c for c in item.addons if c not in addon_prices]
        if missing:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "unknown_addon",
                    "message": f"Unknown or inactive add-on(s): {', '.join(missing)}",
                },
            )
        lines.append(
            QuoteLine(
                unit_price_cents=variant_prices[item.variant_id],
                quantity=item.quantity,
                addon_prices_cents=[addon_prices[c] for c in item.addons],
            )
        )

    q = compute_quote(lines, body.delivery_type)
    return CartQuoteResponse(
        subtotal_cents=q.subtotal_cents,
        delivery_cents=q.delivery_cents,
        time_fee_cents=q.time_fee_cents,
        total_cents=q.total_cents,
        currency=q.currency,
    )
