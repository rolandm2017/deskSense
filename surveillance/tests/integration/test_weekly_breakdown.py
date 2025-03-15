import pytest


# The file is testing this:
# @app.get("/dashboard/breakdown/week/{week_of}", response_model=ProductivityBreakdownByWeek)

# But without the hassle of running the server to make a GET request.

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text

from datetime import datetime, timedelta


from typing import List


import os
from dotenv import load_dotenv


from src.services.dashboard_service import DashboardService

from src.db.dao.timeline_entry_dao import TimelineEntryDao
from src.db.dao.program_summary_dao import ProgramSummaryDao
from src.db.dao.chrome_summary_dao import ChromeSummaryDao
from src.db.dao.summary_logs_dao import ProgramLoggingDao, ChromeLoggingDao

from src.db.models import Base, DailyDomainSummary, DailyProgramSummary

from ..mocks.mock_clock import MockClock

# Load environment variables from .env file
load_dotenv()

# Get the test database connection string
ASYNC_TEST_DB_URL = os.getenv(
    'ASYNC_TEST_DB_URL')

SYNC_TEST_DB_URL = os.getenv("SYNC_TEST_DB_URL")

if ASYNC_TEST_DB_URL is None:
    raise ValueError("ASYNC_TEST_DB_URL environment variable is not set")

if SYNC_TEST_DB_URL is None:
    raise ValueError("SYNC_TEST_DB_URL environment variable is not set")


@pytest.fixture(scope="function")
async def async_engine():
    """Create an async PostgreSQL engine for testing"""
    # Create engine that connects to default postgres database
    if ASYNC_TEST_DB_URL is None:
        raise ValueError("ASYNC_TEST_DB_URL was None")
    default_url = ASYNC_TEST_DB_URL.rsplit('/', 1)[0] + '/postgres'
    admin_engine = create_async_engine(
        default_url,
        isolation_level="AUTOCOMMIT"
    )

    async with admin_engine.connect() as conn:
        # Terminate existing connections more safely
        await conn.execute(text("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = 'dsTestDb'
            AND pid <> pg_backend_pid()
        """))

        # Drop and recreate database
        await conn.execute(text("DROP DATABASE IF EXISTS dsTestDb"))
        await conn.execute(text("CREATE DATABASE dsTestDb"))

    await admin_engine.dispose()

    # Create engine for test database
    test_engine = create_async_engine(
        ASYNC_TEST_DB_URL,
        # echo=True,
        isolation_level="AUTOCOMMIT"  # Add this
    )

    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield test_engine
    finally:
        await test_engine.dispose()

        # Clean up by dropping test database
        admin_engine = create_async_engine(
            default_url,  # Connect to default db for cleanup
            isolation_level="AUTOCOMMIT"
        )
        async with admin_engine.connect() as conn:
            await conn.execute(text("""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = 'dsTestDb'
                AND pid <> pg_backend_pid()
            """))
            await conn.execute(text("DROP DATABASE IF EXISTS dsTestDb"))
        await admin_engine.dispose()


@pytest.fixture(scope="function")
async def async_session_maker(async_engine):
    """Create an async session maker"""
    engine = await anext(async_engine)  # Use anext() instead of await
    session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    return session_maker


@pytest.fixture
async def setup_parts(async_session_maker):
    """
    Fixture that initializes a DashboardService instance for testing.
    This connects to the real database.
    """

    session_maker_async: async_sessionmaker = await async_session_maker

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

    yield service, program_summary_dao, chrome_summary_dao

    # Clean up if needed
    # If your DAOs have close methods, you could call them here


# TODO: Write test data and populate the test db. DO NOT use the real db.
# TODO: Write test data and populate the test db. DO NOT use the real db.
# TODO: Write test data and populate the test db. DO NOT use the real db.
# TODO: Write test data and populate the test db. DO NOT use the real db.
# TODO: Write test data and populate the test db. DO NOT use the real db.
# TODO: Write test data and populate the test db. DO NOT use the real db.
# TODO: Write test data and populate the test db. DO NOT use the real db.
# TODO: Write test data and populate the test db. DO NOT use the real db.
# TODO: Write test data and populate the test db. DO NOT use the real db.
# TODO: Write test data and populate the test db. DO NOT use the real db.
# TODO: Write test data and populate the test db. DO NOT use the real db.


@pytest.mark.asyncio
async def test_reading_individual_days(setup_parts):
    program_summary_dao = setup_parts[1]
    chrome_summary_dao = setup_parts[2]
    feb_23_2025_dt = datetime(2025, 2, 23)  # Year, Month, Day
    feb_24 = feb_23_2025_dt + timedelta(days=1)
    feb_25 = feb_23_2025_dt + timedelta(days=2)

    daily_chrome_summaries: List[DailyDomainSummary] = await chrome_summary_dao.read_day(feb_23_2025_dt)
    daily_program_summaries: List[DailyProgramSummary] = await program_summary_dao.read_day(feb_23_2025_dt)


@pytest.mark.asyncio
async def test_week_of_feb_23(setup_parts):
    dashboard_service = setup_parts[0]

    feb_23_2025_dt = datetime(2025, 2, 23)  # Year, Month, Day
    weeks_overview: List[dict] = await dashboard_service.get_weekly_productivity_overview(feb_23_2025_dt)

    # Assert that no  day has more than 24 hours of recorded time


@pytest.mark.asyncio
async def test_week_of_march_2(setup_parts):
    dashboard_service = setup_parts[0]
    march_2_2025_dt = datetime(2025, 3, 2)  # Year, Month, Day

    weeks_overview: List[dict] = await dashboard_service.get_weekly_productivity_overview(march_2_2025_dt)

    # Assert that no  day has more than 24 hours of recorded time
