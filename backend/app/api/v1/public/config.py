from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas import BusinessIdentity, PublicSettings
from app.services import settings as svc

router = APIRouter(prefix="/v1/config", tags=["config"])


@router.get("/business", response_model=BusinessIdentity, operation_id="getBusiness")
async def business(
    session: AsyncSession = Depends(get_session),
) -> BusinessIdentity:
    data = await svc.get_settings(session)
    return BusinessIdentity(**data["business"])


@router.get(
    "/settings", response_model=PublicSettings, operation_id="getPublicSettings"
)
async def public_settings(
    session: AsyncSession = Depends(get_session),
) -> PublicSettings:
    data = await svc.get_settings(session)
    # Public view excludes notification_recipients and business identity.
    return PublicSettings(
        zones=data["zones"],
        slot_pricing=data["slot_pricing"],
        cutoffs=data["cutoffs"],
        blocked_dates=data["blocked_dates"],
    )
