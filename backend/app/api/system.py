"""Unversioned infra endpoints for load balancers / deploy health checks."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session

router = APIRouter(tags=["system"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness: the process is up. No dependency checks."""
    return {"status": "ok"}


@router.get("/readyz")
async def readyz(session: AsyncSession = Depends(get_session)) -> dict[str, object]:
    """Readiness: can we actually serve? Checks the DB (config is validated at
    startup). Redis joins here once background jobs use it (Phase 5)."""
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - report any DB failure as not-ready
        raise HTTPException(
            status_code=503,
            detail={"code": "not_ready", "message": "Database unavailable."},
        ) from exc
    return {"status": "ready", "checks": {"db": "ok", "config": "ok"}}


@router.get("/health", deprecated=True)
async def health() -> dict[str, str]:
    """Deprecated alias of /healthz. Sunset once clients move over."""
    return {"status": "ok"}
