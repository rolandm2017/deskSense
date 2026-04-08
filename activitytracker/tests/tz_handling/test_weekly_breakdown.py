# tests/tz_handling/test_weekly_breakdown.py

"""
The file is testing this:
@app.get("/dashboard/breakdown/week/{week_of}", response_model=ProductivityBreakdownByWeek)

But without the hassle of running the server to make a GET request.

The point of the test is to verify precise accuracy with the outcome of adding
sessions into the db. The data should match exactly, and everything should be understood.

Previously Postgres-backed; now uses in-memory fake DAOs for speed.
The tests exercise DashboardService.get_weekly_productivity_overview business logic,
not storage semantics.
"""

import pytest

from datetime import datetime, timedelta

from typing import List

from activitytracker.object.classes import (
    CompletedChromeSession,
    CompletedProgramSession,
)
from activitytracker.services.dashboard_service import DashboardService
from activitytracker.util.time_wrappers import UserLocalTime

from ..data.weekly_breakdown_chrome import (
    chrome_feb_23,
    chrome_feb_24,
    chrome_feb_26,
    chrome_march_2nd,
    chrome_march_3rd,
    duplicates_chrome_march_2,
    duplicates_chrome_march_3rd,
    feb_chrome_count,
    march_2_chrome_count,
    march_3_chrome_count,
)
from ..data.weekly_breakdown_programs import (
    duplicate_programs_march_2,
    duplicate_programs_march_3rd,
    feb_23_2025,
    feb_24_2025,
    feb_26_2025,
    feb_program_count,
    march_2_2025,
    march_2_program_count,
    march_3_2025,
    march_3_program_count,
    programs_feb_23,
    programs_feb_24,
    programs_feb_26,
    programs_march_2nd,
    programs_march_3rd,
    weekly_breakdown_tz,
)
from ..mocks.fake_persistence import FakeChromeSummaryDao, FakeProgramSummaryDao


def _populate_program_summaries(dao, sessions, must_be_from_month):
    for session in sessions:
        assert isinstance(session, CompletedProgramSession)
        assert isinstance(session.end_time, UserLocalTime)
        assert must_be_from_month == session.end_time.dt.month
        assert "TEST" in session.window_title

        existing = dao.find_todays_entry_for_program(session)
        if existing:
            dao.push_window_ahead_ten_sec(session)
        else:
            dao.start_session(session)


def _populate_chrome_summaries(dao, sessions, must_be_from_month):
    for session in sessions:
        assert isinstance(session, CompletedChromeSession)
        assert must_be_from_month == session.end_time.dt.month

        existing = dao.find_todays_entry_for_domain(session)
        if existing:
            dao.push_window_ahead_ten_sec(session)
        else:
            dao.start_session(session)


@pytest.fixture
def populated_service():
    """Build a DashboardService backed by in-memory fake DAOs."""
    program_summary_dao = FakeProgramSummaryDao()
    chrome_summary_dao = FakeChromeSummaryDao()

    # February data
    feb_programs = programs_feb_23() + programs_feb_24() + programs_feb_26()
    feb_chrome = chrome_feb_23() + chrome_feb_24() + chrome_feb_26()
    _populate_program_summaries(program_summary_dao, feb_programs, 2)
    _populate_chrome_summaries(chrome_summary_dao, feb_chrome, 2)

    # March data
    march_programs = (
        programs_march_2nd()
        + programs_march_3rd()
        + duplicate_programs_march_2()
        + duplicate_programs_march_3rd()
    )
    march_chrome = (
        chrome_march_2nd()
        + chrome_march_3rd()
        + duplicates_chrome_march_2()
        + duplicates_chrome_march_3rd()
    )
    _populate_program_summaries(program_summary_dao, march_programs, 3)
    _populate_chrome_summaries(chrome_summary_dao, march_chrome, 3)

    service = DashboardService(
        timeline_dao=None,
        program_summary_dao=program_summary_dao,
        program_logging_dao=None,
        chrome_summary_dao=chrome_summary_dao,
        chrome_logging_dao=None,
    )

    yield service, program_summary_dao, chrome_summary_dao, {
        "feb_programs": feb_programs,
        "feb_chrome": feb_chrome,
        "march_programs": march_programs,
        "march_chrome": march_chrome,
    }


def test_read_all(populated_service):
    """Verify that population put the right counts into the fake DAOs."""
    _, program_summary_dao, chrome_summary_dao, test_data = populated_service

    all_programs = program_summary_dao.read_all()

    just_retrieved_names = [x.program_name for x in all_programs]
    for dummy in test_data["feb_programs"] + test_data["march_programs"]:
        assert dummy.window_title in just_retrieved_names, "A program was missing"

    # Sort by date and verify counts
    feb_vals = [p for p in all_programs if p.gathering_date.month == 2]
    march_2_vals = [
        p
        for p in all_programs
        if p.gathering_date.month == 3 and p.gathering_date.day == 2
    ]
    march_3_vals = [
        p
        for p in all_programs
        if p.gathering_date.month == 3 and p.gathering_date.day == 3
    ]

    assert len(feb_vals) == feb_program_count
    assert len(march_2_vals) == march_2_program_count
    assert len(march_3_vals) == march_3_program_count

    # Verify uniqueness within a single day
    for day_vals in (march_2_vals, march_3_vals):
        exe_paths = [x.exe_path_as_id for x in day_vals]
        assert len(set(exe_paths)) == len(exe_paths), "Duplicate exe paths in a single day"

    total_unique = feb_program_count + march_2_program_count + march_3_program_count
    assert len(all_programs) == total_unique

    # Chrome section
    all_domains = chrome_summary_dao.read_all()
    feb_chrome_vals = [d for d in all_domains if d.gathering_date.month == 2]
    march_2_chrome = [
        d
        for d in all_domains
        if d.gathering_date.month == 3 and d.gathering_date.day == 2
    ]
    march_3_chrome = [
        d
        for d in all_domains
        if d.gathering_date.month == 3 and d.gathering_date.day == 3
    ]

    assert len(feb_chrome_vals) == feb_chrome_count
    assert len(march_2_chrome) == march_2_chrome_count
    assert len(march_3_chrome) == march_3_chrome_count


def test_reading_individual_days(populated_service):
    _, program_summary_dao, chrome_summary_dao, _ = populated_service

    march_2_ult = UserLocalTime(march_2_2025 + timedelta(minutes=43))

    daily_programs = program_summary_dao.read_day(march_2_ult)
    daily_chrome = chrome_summary_dao.read_day(march_2_ult)

    assert len(daily_programs) == march_2_program_count
    assert len(daily_chrome) == march_2_chrome_count

    march_3_modified = UserLocalTime(
        march_3_2025 + timedelta(hours=1, minutes=9, seconds=33)
    )

    daily_programs_2 = program_summary_dao.read_day(march_3_modified)
    daily_chrome_2 = chrome_summary_dao.read_day(march_3_modified)

    assert len(daily_programs_2) == march_3_program_count
    assert len(daily_chrome_2) == march_3_chrome_count

    assert (
        len(daily_programs) + len(daily_chrome)
        == march_2_program_count + march_2_chrome_count
    )
    assert (
        len(daily_programs_2) + len(daily_chrome_2)
        == march_3_program_count + march_3_chrome_count
    )

    # A day with no data
    empty_day = UserLocalTime(march_3_2025 + timedelta(days=1))
    assert len(program_summary_dao.read_day(empty_day)) == 0
    assert len(chrome_summary_dao.read_day(empty_day)) == 0


@pytest.mark.asyncio
async def test_week_of_feb_23(populated_service):
    service, _, _, _ = populated_service

    feb_23_2025_dt = weekly_breakdown_tz.localize(datetime(2025, 2, 23))

    weeks_overview: List[dict] = await service.get_weekly_productivity_overview(
        feb_23_2025_dt
    )

    assert all(isinstance(d, dict) for d in weeks_overview)
    assert all(
        "day" in d and "productivity" in d and "leisure" in d for d in weeks_overview
    )

    sums = [d["productivity"] + d["leisure"] for d in weeks_overview]
    assert all(x < 16 for x in sums), "Some day had 16 hours or more of time recorded"


@pytest.mark.asyncio
async def test_week_of_march_2(populated_service):
    service = populated_service[0]
    march_2_2025_dt = weekly_breakdown_tz.localize(datetime(2025, 3, 2))

    weeks_overview: List[dict] = await service.get_weekly_productivity_overview(
        march_2_2025_dt
    )

    assert all(isinstance(d, dict) for d in weeks_overview)
    assert all(
        "day" in d and "productivity" in d and "leisure" in d for d in weeks_overview
    )

    sums = [d["productivity"] + d["leisure"] for d in weeks_overview]
    assert all(x < 16 for x in sums), "Some day had 16 hours or more of time recorded"
