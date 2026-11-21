from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import ids
from app.db import get_session
from app.models import OrderStatus
from app.repositories import orders as repo
from app.schemas import TimelineStep, TrackItem, TrackResponse

router = APIRouter(prefix="/v1/orders", tags=["orders"])

# Happy-path order for the tracking timeline.
_HAPPY = [
    OrderStatus.NEW,
    OrderStatus.ACCEPTED,
    OrderStatus.AWAITING_PHOTO,
    OrderStatus.PHOTO_SENT,
    OrderStatus.APPROVED,
    OrderStatus.OUT_FOR_DELIVERY,
    OrderStatus.DELIVERED,
]


@router.get("/track/{token}", response_model=TrackResponse, operation_id="trackOrder")
async def track(
    token: str, session: AsyncSession = Depends(get_session)
) -> TrackResponse:
    order = await repo.get_by_token_hash(session, ids.hash_token(token))
    if order is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "order_not_found", "message": "Order not found."},
        )
    current = order.status
    idx = _HAPPY.index(current) if current in _HAPPY else -1
    timeline = [
        TimelineStep(status=s.value, done=(i <= idx)) for i, s in enumerate(_HAPPY)
    ]
    # Public-safe: no sender email, no payment details.
    return TrackResponse(
        order_number=order.number,
        status=current.value,
        timeline=timeline,
        bouquet_photo=order.bouquet_photo,
        delivery_slot=order.slot_start.isoformat() if order.slot_start else None,
        total_cents=order.total_cents,
        items=[
            TrackItem(name=i.name_snapshot, tier=i.tier_snapshot or "")
            for i in order.items
        ],
    )
