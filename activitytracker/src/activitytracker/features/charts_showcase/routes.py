from datetime import date

from fastapi import APIRouter, Depends, Query

from activitytracker.features.charts_showcase.schemas import (
    ActiveIdleResponse,
    TopActivitiesResponse,
)
from activitytracker.features.charts_showcase.service import (
    ChartsShowcaseService,
    get_charts_showcase_service,
)


router = APIRouter(prefix="/api/daily", tags=["charts-showcase"])


@router.get("/active-idle", response_model=ActiveIdleResponse)
async def get_daily_active_idle(
    day: date = Query(..., alias="date"),
    service: ChartsShowcaseService = Depends(get_charts_showcase_service),
) -> ActiveIdleResponse:
    return service.get_active_idle(day)


@router.get("/top-activities", response_model=TopActivitiesResponse)
async def get_daily_top_activities(
    day: date = Query(..., alias="date"),
    limit: int = Query(12, ge=1, le=50),
    service: ChartsShowcaseService = Depends(get_charts_showcase_service),
) -> TopActivitiesResponse:
    return service.get_top_activities(day, limit)
