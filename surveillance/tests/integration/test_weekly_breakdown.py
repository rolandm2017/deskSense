# tests/integration/test_weekly_breakdown.py

# The file is testing this:
# @app.get("/dashboard/breakdown/week/{week_of}", response_model=ProductivityBreakdownByWeek)

# But without the hassle of running the server to make a GET request.
import pytest
import pytest_asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text

from datetime import datetime, timedelta


from typing import List


import os
from dotenv import load_dotenv


from surveillance.src.services.dashboard_service import DashboardService

from surveillance.src.db.dao.queuing.timeline_entry_dao import TimelineEntryDao
from surveillance.src.db.dao.direct.program_summary_dao import ProgramSummaryDao
from surveillance.src.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from surveillance.src.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao

from surveillance.src.db.models import Base, DailyDomainSummary, DailyProgramSummary
from surveillance.src.object.classes import ChromeSessionData, ProgramSessionData
from ..data.weekly_breakdown_programs import (
    duplicate_programs_march_2, duplicate_programs_march_3rd,
    programs_march_2nd, programs_march_3rd,
    march_2_2025, march_3_2025,
    march_2_program_count, march_3_program_count, unique_programs, feb_program_count,
    programs_feb_23, programs_feb_24, programs_feb_26
)
from ..data.weekly_breakdown_chrome import (
    duplicates_chrome_march_2, duplicates_chrome_march_3rd,
    chrome_march_2nd, chrome_march_3rd,
    march_2_chrome_count, march_3_chrome_count, unique_domains, feb_chrome_count,
    chrome_feb_23, chrome_feb_24, chrome_feb_26
)


from ..mocks.mock_clock import MockClock

# Load environment variables from .env file
load_dotenv()

# FIXME: Turtle slow test: use in memory db?

# # Get the test database connection string

# SYNC_TEST_DB_URL = os.getenv("SYNC_TEST_DB_URL")

# if SYNC_TEST_DB_URL is None:
#     raise ValueError("SYNC_TEST_DB_URL environment variable is not set")





@pytest_asyncio.fixture
async def setup_parts(async_engine_and_asm):
    """
    Fixture that initializes a DashboardService instance for testing.
    This connects to the test db, unless there is an unforseen problem.
    """
    _, asm = async_engine_and_asm

    session_maker_async: async_sessionmaker = asm

    # Get all required DAOs
    timeline_dao = TimelineEntryDao(session_maker_async)
    program_logging_dao = ProgramLoggingDao(session_maker_async)
    chrome_logging_dao = ChromeLoggingDao(session_maker_async)
    program_summary_dao = ProgramSummaryDao(
        program_logging_dao, session_maker_async)
    chrome_summary_dao = ChromeSummaryDao(
        chrome_logging_dao, session_maker_async)

    # Create and return the dashboard service
    service = DashboardService(
        timeline_dao=timeline_dao,
        program_summary_dao=program_summary_dao,
        program_logging_dao=program_logging_dao,
        chrome_summary_dao=chrome_summary_dao,
        chrome_logging_dao=chrome_logging_dao
    )

    yield service, program_summary_dao, chrome_summary_dao, session_maker_async
    # Clean up if needed
    # If your DAOs have close methods, you could call them here


async def truncate_test_tables(session_maker_async):
    """Truncate all test tables directly"""
    # NOTE: IF you run the tests in a broken manner,
    # ####  the first run AFTER fixing the break
    # ####  MAY still look broken.
    # ####  Because the truncation happens *at the end of* a test.

    async with session_maker_async() as session:
        await session.execute(text("TRUNCATE daily_program_summaries RESTART IDENTITY CASCADE"))
        await session.execute(text("TRUNCATE daily_chrome_summaries RESTART IDENTITY CASCADE"))
        await session.execute(text("TRUNCATE program_summary_logs RESTART IDENTITY CASCADE"))
        await session.execute(text("TRUNCATE domain_summary_logs RESTART IDENTITY CASCADE"))
        await session.execute(text("TRUNCATE system_change_log RESTART IDENTITY CASCADE"))
        await session.commit()
        print("Super truncated tables")


@pytest_asyncio.fixture
async def setup_with_populated_db(setup_parts):

    # Write test data and populate the test db. DO NOT use the real db. You will mess it up.
    # Write test data and populate the test db. DO NOT use the real db. You will mess it up.
    # Write test data and populate the test db. DO NOT use the real db. You will mess it up.
    # Write test data and populate the test db. DO NOT use the real db. You will mess it up.
    service, program_summary_dao, chrome_summary_dao, session_maker_async = setup_parts

    await truncate_test_tables(session_maker_async)

    test_data_feb_programs = programs_feb_23() + programs_feb_24() + \
        programs_feb_26()
    test_data_feb_chrome = chrome_feb_23() + chrome_feb_24() + \
        chrome_feb_26()

    for s in test_data_feb_programs:
        await program_summary_dao.create_if_new_else_update(s, s.end_time)
    for s in test_data_feb_chrome:
        await chrome_summary_dao.create_if_new_else_update(s, s.end_time)

    test_data_programs = programs_march_2nd() + programs_march_3rd() + \
        duplicate_programs_march_2() + duplicate_programs_march_3rd()
    test_data_chrome = chrome_march_2nd() + \
        chrome_march_3rd() + duplicates_chrome_march_2() + \
        duplicates_chrome_march_3rd()

    assert all(isinstance(s, ProgramSessionData)
               for s in test_data_programs), "There was a bug in setup"
    assert all(isinstance(s, ChromeSessionData)
               for s in test_data_chrome), "There was a bug in setup"

    programs_sum = timedelta()
    chrome_sum = timedelta()
    for session in test_data_programs:
        programs_sum = programs_sum + session.duration
    for session in test_data_chrome:
        chrome_sum = chrome_sum + session.duration
    print(programs_sum, chrome_sum)
    for session in test_data_programs:
        right_now_arg = session.end_time  # type:ignore
        programs_sum = programs_sum + session.duration
        # print(session.window_title, session.duration)
        await program_summary_dao.create_if_new_else_update(session, right_now_arg)

    for session in test_data_chrome:
        right_now_arg = session.end_time  # type:ignore
        # print(session.domain, session.duration)
        await chrome_summary_dao.create_if_new_else_update(session, right_now_arg)

    yield service, program_summary_dao, chrome_summary_dao

    await program_summary_dao.program_logging_dao.cleanup()
    await chrome_summary_dao.chrome_logging_dao.cleanup()
    # await program_summary_dao.cleanup()
    # await chrome_summary_dao.cleanup()


@pytest.mark.asyncio
async def test_read_all(setup_with_populated_db):
    """This test is mostly testing setup conditions for other tests."""
    # parts = await anext(setup_with_populated_db)
    _, program_summary_dao, chrome_summary_dao = setup_with_populated_db

    # # But first, do some basic sanity checks:
    all_for_verification = await program_summary_dao.read_all()

    feb_vals = []

    march_2_vals = []
    march_3rd_vals = []

    # FIXME:
    for v in all_for_verification:
        if v.gathering_date.month == 2:
            feb_vals.append(v)
        elif v.gathering_date.day == 2:
            march_2_vals.append(v)
        elif v.gathering_date.day == 3:
            march_3rd_vals.append(v)
        else:
            print(v, 'unexpected date for gathering_date')

    # So they're actually, like, there.
    assert len(feb_vals) == feb_program_count
    assert len(
        march_2_vals) == march_2_program_count, "A Program was missing"
    assert len(
        march_3rd_vals) == march_3_program_count, "A Program was missing"

    feb_vals_chrome = []

    chrome_march2_vals = []
    chrome_march_3rd_vals = []

    all_domains_for_verify = await chrome_summary_dao.read_all()

    for v in all_domains_for_verify:
        if v.gathering_date.month == 2:
            feb_vals_chrome.append(v)
        elif v.gathering_date.day == 2:
            chrome_march2_vals.append(v)
        elif v.gathering_date.day == 3:
            chrome_march_3rd_vals.append(v)
        else:
            print(v, 'unexpected date for start_time')

    assert len(feb_vals_chrome) == feb_chrome_count
    assert len(
        chrome_march2_vals) == march_2_chrome_count, "A Chrome entry was missing"
    assert len(
        chrome_march_3rd_vals) == march_3_chrome_count, "A Chrome entry was missing"

    assert all(x.gathering_date.day ==
               2 for x in chrome_march2_vals), "Failed to sort"
    assert all(x.gathering_date.day ==
               3 for x in chrome_march_3rd_vals), "Failed to sort"


@pytest.mark.asyncio
async def test_reading_individual_days(setup_with_populated_db):
    _, program_summary_dao, chrome_summary_dao = setup_with_populated_db

    test_day_3 = march_3_2025 + timedelta(days=1)

    # NOTE that this date is in the test data for sure! it's circular.

    daily_program_summaries: List[DailyProgramSummary] = await program_summary_dao.read_day(march_2_2025)
    daily_chrome_summaries: List[DailyDomainSummary] = await chrome_summary_dao.read_day(march_2_2025)

    print(len(daily_program_summaries), march_2_program_count)
    assert len(daily_program_summaries) == march_2_program_count
    assert len(daily_chrome_summaries) == march_2_chrome_count

    # ### Assert that the expected programs, domains are all in there

    # ### Continue asserting that expected domains, programs are all in there

    march_3_modified = march_3_2025 + timedelta(hours=1, minutes=9, seconds=33)

    daily_program_summaries_2: List[DailyProgramSummary] = await program_summary_dao.read_day(march_3_modified)
    daily_chrome_summaries_2: List[DailyDomainSummary] = await chrome_summary_dao.read_day(march_3_modified)

    assert len(
        daily_program_summaries_2) == march_3_program_count, "A program session didn't load"
    assert len(
        daily_chrome_summaries_2) == march_3_chrome_count, "A Chrome session didn't load"

    count_of_march_2 = march_2_program_count + march_2_chrome_count
    count_of_march_3 = march_3_program_count + march_3_chrome_count

    assert len(daily_program_summaries) + \
        len(daily_chrome_summaries) == count_of_march_2
    assert len(daily_program_summaries_2) + \
        len(daily_chrome_summaries_2) == count_of_march_3

    zero_pop_day_programs: List[DailyProgramSummary] = await program_summary_dao.read_day(test_day_3)
    zero_pop_day_chrome: List[DailyDomainSummary] = await chrome_summary_dao.read_day(test_day_3)

    assert len(zero_pop_day_programs) + len(zero_pop_day_chrome) == 0


@pytest.mark.asyncio
async def test_week_of_feb_23(setup_with_populated_db):
    service, _, _ = setup_with_populated_db
    dashboard_service = service

    feb_23_2025_dt = datetime(2025, 2, 23)  # Year, Month, Day
    # ### ###
    # # Check the test data to see what's in here
    # ### ###
    weeks_overview: List[dict] = await dashboard_service.get_weekly_productivity_overview(feb_23_2025_dt)

    assert all(isinstance(d, dict)
               for d in weeks_overview), "Expected types not found"
    assert all(
        "day" in d and "productivity" in d and "leisure" in d for d in weeks_overview), "Expected keys not found"

    # Assert that no  day has more than 16 hours of recorded time
    sums = [d["productivity"] + d["leisure"] for d in weeks_overview]
    assert all(
        x < 16 for x in sums), "Some day had 16 hours or more of time recorded"


# # @pytest.mark.asyncio
# # async def test_week_of_march_2(setup_with_populated_db):
# #     dashboard_service = setup_with_populated_db[0]
# #     march_2_2025_dt = datetime(2025, 3, 2)  # Year, Month, Day

# #     weeks_overview: List[dict] = await dashboard_service.get_weekly_productivity_overview(march_2_2025_dt)

# #     # Assert that no  day has more than 24 hours of recorded time
