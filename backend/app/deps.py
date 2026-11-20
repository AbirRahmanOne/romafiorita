"""Request-level auth dependencies: current staff, role guards, CSRF."""

from __future__ import annotations

import secrets
from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import security
from app.db import get_session
from app.models import Staff, StaffRole

ACCESS_COOKIE = "rf_access"
REFRESH_COOKIE = "rf_refresh"
CSRF_COOKIE = "rf_csrf"
CSRF_HEADER = "x-csrf-token"


def _unauthorized(message: str = "Not authenticated.") -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={"code": "not_authenticated", "message": message},
    )


async def get_current_staff(
    request: Request, session: AsyncSession = Depends(get_session)
) -> Staff:
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise _unauthorized()
    try:
        payload = security.decode_token(token, "access")
    except security.TokenError as exc:
        raise _unauthorized("Invalid or expired session.") from exc
    staff = await session.get(Staff, int(payload["sub"]))
    if staff is None or not staff.is_active:
        raise _unauthorized("Account not found or disabled.")
    return staff


def require_roles(
    *roles: StaffRole,
) -> Callable[[Staff], Awaitable[Staff]]:
    """Dependency factory: allow only the given roles."""

    async def guard(staff: Staff = Depends(get_current_staff)) -> Staff:
        if staff.role not in roles:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "forbidden",
                    "message": "Insufficient role for this action.",
                },
            )
        return staff

    return guard


async def csrf_protect(request: Request) -> None:
    """Double-submit cookie check for cookie-authenticated mutations."""
    cookie = request.cookies.get(CSRF_COOKIE)
    header = request.headers.get(CSRF_HEADER)
    if not cookie or not header or not secrets.compare_digest(cookie, header):
        raise HTTPException(
            status_code=403,
            detail={"code": "csrf_failed", "message": "Missing or invalid CSRF token."},
        )
