"""
Regression test for the PeripheralsService.get_current_week_timeline bug:
prepare_start_of_week returns a naive (tz-unaware) datetime, and
get_current_week_timeline was not localizing it before wrapping in UserLocalTime.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

from activitytracker.config.definitions import local_time_zone
from activitytracker.services.dashboard_service import PeripheralsService
from activitytracker.services.timezone_service import TimezoneService
from activitytracker.util.time_wrappers import UserLocalTime
from activitytracker.util.errors import TimezoneUnawareError


def _make_service() -> PeripheralsService:
    """Build a PeripheralsService with mocked DAOs and a real TimezoneService."""
    timeline_dao = MagicMock()
    # DAO methods are async — make them return empty lists by default
    timeline_dao.read_day_mice = AsyncMock(return_value=[])
    timeline_dao.read_day_keyboard = AsyncMock(return_value=[])

    timezone_service = TimezoneService()

    svc = PeripheralsService(timeline_dao, timezone_service)

    # Replace the real clock with one that returns a known tz-aware time
    fake_clock = MagicMock()
    tz = ZoneInfo(local_time_zone)
    fake_now = UserLocalTime(datetime(2026, 4, 7, 14, 30, 0, tzinfo=tz))
    fake_clock.now.return_value = fake_now
    svc.user_clock = fake_clock

    return svc


@pytest.mark.asyncio
async def test_get_current_week_timeline_does_not_raise_timezone_unaware():
    """
    get_current_week_timeline must localize the naive datetime from
    prepare_start_of_week before wrapping it in UserLocalTime.

    Without the fix this raises TimezoneUnawareError.
    """
    svc = _make_service()
    # This should NOT raise TimezoneUnawareError
    days_before_today, today_payload, starting_sunday = (
        await svc.get_current_week_timeline()
    )
    assert starting_sunday is not None
