from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import require_roles
from app.models import StaffRole
from app.schemas import DashboardResponse, SalesInsights, SeoInsights
from app.services import analytics

router = APIRouter(prefix="/v1/admin", tags=["admin-insights"])

_can = Depends(require_roles(StaffRole.OWNER, StaffRole.MANAGER))


@router.get("/dashboard", response_model=DashboardResponse, dependencies=[_can])
async def dashboard(
    session: AsyncSession = Depends(get_session),
) -> DashboardResponse:
    return DashboardResponse(**await analytics.compute_dashboard(session))


@router.get("/insights/sales", response_model=SalesInsights, dependencies=[_can])
async def sales_insights(
    range: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_session),
) -> SalesInsights:
    return SalesInsights(**await analytics.compute_sales(session, range))


@router.get("/insights/seo", response_model=SeoInsights, dependencies=[_can])
async def seo_insights() -> SeoInsights:
    # Google Search Console not connected yet — empty, not fabricated.
    return SeoInsights(connected=False)
