from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps import rate_limit
from app.domain import delivery
from app.schemas import (
    DeliveryCheckResponse,
    DeliveryFees,
    SlotListResponse,
    SlotRead,
)

router = APIRouter(prefix="/v1/delivery", tags=["delivery"])


def _reject_invalid_postcode() -> HTTPException:
    return HTTPException(
        status_code=422,
        detail={
            "code": "invalid_postcode",
            "message": "Not a valid Italian postcode (CAP).",
        },
    )


def _fees() -> DeliveryFees:
    return DeliveryFees(
        standard_cents=0,
        window_cents=delivery.WINDOW_FEE_CENTS,
        exact_cents=delivery.EXACT_FEE_CENTS,
    )


@router.get(
    "/check",
    response_model=DeliveryCheckResponse,
    operation_id="checkDelivery",
    dependencies=[Depends(rate_limit("delivery_check", limit=60))],
)
async def check(
    postcode: str,
    date_: date | None = Query(default=None, alias="date"),
) -> DeliveryCheckResponse:
    zone = delivery.zone_for(postcode)
    if zone is None:
        raise _reject_invalid_postcode()
    day = date_ or datetime.now(delivery.ROME_TZ).date()
    is_rome = zone is delivery.Zone.ROME
    cutoff = delivery.same_day_cutoff(day).isoformat() if is_rome else None
    return DeliveryCheckResponse(
        zone=zone.value,
        types=[t.value for t in delivery.delivery_types(zone)],
        fees=_fees(),
        cutoff=cutoff,
    )


@router.get("/slots", response_model=SlotListResponse, operation_id="deliverySlots")
async def slots(
    postcode: str,
    date_: date | None = Query(default=None, alias="date"),
) -> SlotListResponse:
    zone = delivery.zone_for(postcode)
    if zone is None:
        raise _reject_invalid_postcode()
    if zone is not delivery.Zone.ROME:
        return SlotListResponse(slots=[])  # national = courier, date only
    day = date_ or datetime.now(delivery.ROME_TZ).date()
    generated = delivery.generate_slots(day, datetime.now(UTC))
    return SlotListResponse(
        slots=[
            SlotRead(time=s.time, iso=s.iso, available=s.available) for s in generated
        ]
    )
