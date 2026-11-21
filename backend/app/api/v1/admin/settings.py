from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import csrf_protect, require_roles
from app.models import StaffRole
from app.schemas import SettingsRead, SettingsUpdate
from app.services import settings as svc

router = APIRouter(prefix="/v1/admin/settings", tags=["admin-settings"])

_can = Depends(require_roles(StaffRole.OWNER, StaffRole.MANAGER))
_csrf = Depends(csrf_protect)


@router.get("", response_model=SettingsRead, dependencies=[_can])
async def get_settings(
    session: AsyncSession = Depends(get_session),
) -> SettingsRead:
    return SettingsRead(**await svc.get_settings(session))


@router.patch("", response_model=SettingsRead, dependencies=[_can, _csrf])
async def update_settings(
    data: SettingsUpdate, session: AsyncSession = Depends(get_session)
) -> SettingsRead:
    patch = data.model_dump(exclude_unset=True)
    return SettingsRead(**await svc.update_settings(session, patch))
