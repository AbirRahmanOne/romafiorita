from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import csrf_protect, require_roles
from app.models import StaffRole
from app.schemas import GdprDeleteRequest, GdprDeleteResponse, GdprExportResponse
from app.services import gdpr

router = APIRouter(prefix="/v1/admin/gdpr", tags=["admin-gdpr"])

# GDPR actions are OWNER-only.
_owner = Depends(require_roles(StaffRole.OWNER))
_csrf = Depends(csrf_protect)


@router.get("/export", response_model=GdprExportResponse, dependencies=[_owner])
async def export(
    email: str = Query(min_length=3),
    session: AsyncSession = Depends(get_session),
) -> GdprExportResponse:
    data = await gdpr.export_customer(session, email)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "customer_not_found", "message": "No such customer."},
        )
    return GdprExportResponse(**data)


@router.post(
    "/delete", response_model=GdprDeleteResponse, dependencies=[_owner, _csrf]
)
async def delete(
    body: GdprDeleteRequest, session: AsyncSession = Depends(get_session)
) -> GdprDeleteResponse:
    anonymised = await gdpr.delete_customer(session, body.email)
    if not anonymised:
        raise HTTPException(
            status_code=404,
            detail={"code": "customer_not_found", "message": "No such customer."},
        )
    return GdprDeleteResponse(anonymised=True)
