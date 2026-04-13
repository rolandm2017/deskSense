from datetime import date

import pytest

from activitytracker.features.charts_showcase.routes import (
    get_daily_active_idle,
    get_daily_top_activities,
    router,
)
from activitytracker.features.charts_showcase.service import ChartsShowcaseService


def test_router_exposes_activity_overview_paths():
    paths = {route.path for route in router.routes}

    assert "/api/daily/active-idle" in paths
    assert "/api/daily/top-activities" in paths


@pytest.mark.asyncio
async def test_active_idle_endpoint_returns_daily_lane_contract():
    response = await get_daily_active_idle(
        day=date(2026, 4, 7),
        service=ChartsShowcaseService(),
    )
    payload = response.model_dump()

    assert payload["date"] == "2026-04-07"
    assert payload["range"] == {
        "start": "2026-04-07T04:00:00",
        "end": "2026-04-08T04:00:00",
    }
    assert payload["totals"]["trackedSeconds"] == (
        payload["totals"]["activeSeconds"] + payload["totals"]["idleSeconds"]
    )
    assert payload["blocks"][0] == {
        "start": "2026-04-07T07:42:00",
        "end": "2026-04-07T10:30:00",
        "state": "active",
        "durationSeconds": 10080,
    }


@pytest.mark.asyncio
async def test_top_activities_endpoint_returns_ranked_limited_lanes():
    response = await get_daily_top_activities(
        day=date(2026, 4, 7),
        limit=3,
        service=ChartsShowcaseService(),
    )
    payload = response.model_dump()

    assert payload["date"] == "2026-04-07"
    assert payload["limit"] == 3
    assert payload["mergeGapSeconds"] == 300
    assert [lane["rank"] for lane in payload["lanes"]] == [1, 2, 3]
    assert [lane["displayName"] for lane in payload["lanes"]] == [
        "VS Code",
        "Chrome",
        "Factorio",
    ]
    assert payload["lanes"][0]["blocks"][0]["label"] == "DeskSense - main.ts"
