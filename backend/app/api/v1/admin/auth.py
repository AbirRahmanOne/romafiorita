"""Admin authentication: login, logout, refresh (rotating), me.

Tokens live in httpOnly cookies. Refresh tokens rotate on every use and a
reuse of a stale token revokes the session (reuse detection via `refresh_jti`).
Login failures are rate-limited by a per-account lockout.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core import security
from app.db import get_session
from app.deps import (
    ACCESS_COOKIE,
    CSRF_COOKIE,
    REFRESH_COOKIE,
    csrf_protect,
    get_current_staff,
)
from app.models import Staff
from app.schemas import LoginRequest, StaffMe

router = APIRouter(prefix="/v1/admin/auth", tags=["auth"])

# Refresh cookie only travels to the auth endpoints.
_REFRESH_PATH = "/v1/admin/auth"


def _invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={"code": "invalid_credentials", "message": "Invalid email or password."},
    )


def _cookie(
    response: Response,
    name: str,
    value: str,
    *,
    path: str,
    max_age: int,
    httponly: bool,
) -> None:
    response.set_cookie(
        name,
        value,
        max_age=max_age,
        path=path,
        domain=settings.cookie_domain,
        secure=settings.secure_cookies,
        httponly=httponly,
        samesite="lax",
    )


def _set_session_cookies(response: Response, staff: Staff, jti: str) -> None:
    access = security.create_access_token(staff.id, staff.role.value)
    refresh = security.create_refresh_token(staff.id, jti)
    refresh_age = settings.refresh_token_ttl_days * 86400
    _cookie(
        response, ACCESS_COOKIE, access, path="/",
        max_age=settings.access_token_ttl_minutes * 60, httponly=True,
    )
    _cookie(
        response, REFRESH_COOKIE, refresh, path=_REFRESH_PATH,
        max_age=refresh_age, httponly=True,
    )
    # Not httpOnly: the SPA reads it and echoes it in the X-CSRF-Token header.
    _cookie(
        response, CSRF_COOKIE, security.new_csrf_token(), path="/",
        max_age=refresh_age, httponly=False,
    )


def _clear_session_cookies(response: Response) -> None:
    dom = settings.cookie_domain
    response.delete_cookie(ACCESS_COOKIE, path="/", domain=dom)
    response.delete_cookie(REFRESH_COOKIE, path=_REFRESH_PATH, domain=dom)
    response.delete_cookie(CSRF_COOKIE, path="/", domain=dom)


@router.post("/login", response_model=StaffMe)
async def login(
    data: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> Staff:
    staff = await session.scalar(select(Staff).where(Staff.email == data.email))
    now = datetime.now(UTC)

    # SQLite returns naive datetimes; stored values are UTC.
    locked_until = staff.locked_until if staff else None
    if locked_until and locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=UTC)

    if locked_until and locked_until > now:
        raise HTTPException(
            status_code=429,
            detail={
                "code": "account_locked",
                "message": "Too many attempts. Try later.",
            },
        )

    if staff is None or not staff.is_active or not security.verify_password(
        staff.hashed_password, data.password
    ):
        if staff is not None:
            staff.failed_login_count += 1
            if staff.failed_login_count >= settings.login_max_attempts:
                staff.locked_until = now + timedelta(
                    minutes=settings.login_lockout_minutes
                )
                staff.failed_login_count = 0
            await session.commit()
        raise _invalid_credentials()

    # Success: reset counters, rotate refresh.
    staff.failed_login_count = 0
    staff.locked_until = None
    jti = security.new_jti()
    staff.refresh_jti = jti
    await session.commit()
    _set_session_cookies(response, staff, jti)
    return staff


@router.post("/refresh", response_model=StaffMe)
async def refresh(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_session),
    _: None = Depends(csrf_protect),
) -> Staff:
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        raise _invalid_credentials()
    try:
        payload = security.decode_token(token, "refresh")
    except security.TokenError as exc:
        raise _invalid_credentials() from exc

    staff = await session.get(Staff, int(payload["sub"]))
    if staff is None or not staff.is_active:
        raise _invalid_credentials()

    # Reuse detection: a token whose jti no longer matches is stale/stolen.
    if staff.refresh_jti is None or staff.refresh_jti != payload.get("jti"):
        staff.refresh_jti = None  # revoke the session
        await session.commit()
        _clear_session_cookies(response)
        raise _invalid_credentials()

    jti = security.new_jti()
    staff.refresh_jti = jti
    await session.commit()
    _set_session_cookies(response, staff, jti)
    return staff


@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    session: AsyncSession = Depends(get_session),
    staff: Staff = Depends(get_current_staff),
    _: None = Depends(csrf_protect),
) -> Response:
    staff.refresh_jti = None
    await session.commit()
    # Mutate (don't replace) the injected response so the clears survive.
    _clear_session_cookies(response)
    response.status_code = 204
    return response


@router.get("/me", response_model=StaffMe)
async def me(staff: Staff = Depends(get_current_staff)) -> Staff:
    return staff
