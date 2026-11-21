from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db import get_session
from app.deps import csrf_protect, require_roles
from app.models import Staff, StaffRole
from app.schemas import StaffCreate, StaffListResponse, StaffRead, StaffUpdate

router = APIRouter(prefix="/v1/admin/staff", tags=["admin-staff"])

# Staff management is OWNER-only.
_owner = Depends(require_roles(StaffRole.OWNER))
_csrf = Depends(csrf_protect)


@router.get("", response_model=StaffListResponse, dependencies=[_owner])
async def list_staff(
    session: AsyncSession = Depends(get_session),
) -> StaffListResponse:
    rows = await session.scalars(select(Staff).order_by(Staff.id))
    return StaffListResponse(items=[StaffRead.model_validate(s) for s in rows.all()])


@router.post(
    "", response_model=StaffRead, status_code=201, dependencies=[_owner, _csrf]
)
async def create_staff(
    data: StaffCreate, session: AsyncSession = Depends(get_session)
) -> StaffRead:
    exists = await session.scalar(select(Staff.id).where(Staff.email == data.email))
    if exists is not None:
        raise HTTPException(
            status_code=409,
            detail={"code": "email_taken", "message": "Email already in use."},
        )
    staff = Staff(
        email=data.email,
        name=data.name,
        role=data.role,
        hashed_password=hash_password(data.password),
    )
    session.add(staff)
    await session.commit()
    return StaffRead.model_validate(staff)


@router.patch("/{staff_id}", response_model=StaffRead, dependencies=[_owner, _csrf])
async def update_staff(
    staff_id: int,
    data: StaffUpdate,
    session: AsyncSession = Depends(get_session),
) -> StaffRead:
    staff = await session.get(Staff, staff_id)
    if staff is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Staff member not found."},
        )
    fields = data.model_dump(exclude_unset=True)
    if "password" in fields:
        staff.hashed_password = hash_password(fields.pop("password"))
    for key, value in fields.items():
        setattr(staff, key, value)
    await session.commit()
    return StaffRead.model_validate(staff)
