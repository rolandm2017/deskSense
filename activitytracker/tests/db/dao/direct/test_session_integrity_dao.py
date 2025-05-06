import psutil
import pytest
import pytest_asyncio

import asyncio

import pytz
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select, text, func

from dotenv import load_dotenv
import os

# Import models and DAOs
from activitytracker.db.models import Base, SystemStatus, ProgramSummaryLog, DomainSummaryLog
from activitytracker.db.dao.direct.session_integrity_dao import SessionIntegrityDao
from activitytracker.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from activitytracker.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from activitytracker.tz_handling.time_formatting import get_start_of_day_from_datetime

from ....helper.truncation import truncate_logs_tables_via_engine

# Load environment variables from .env file
load_dotenv()


process = psutil.Process()
open_files = process.open_files()
num_open_files = len(open_files)
print(f"Num of open files: {num_open_files}")


# Get the test database connection string
ASYNC_TEST_DB_URL = os.getenv('ASYNC_TEST_DB_URL')
SYNC_TEST_DB_URL = os.getenv("SYNC_TEST_DB_URL")

if ASYNC_TEST_DB_URL is None:
    raise ValueError("ASYNC_TEST_DB_URL environment variable is not set")

if SYNC_TEST_DB_URL is None:
    raise ValueError("SYNC_TEST_DB_URL environment variable is not set")

# FIXME: Test is slow as a turtle
# # TODO: make these tests extremely minimal. Test with 2-4 writes involved MAX. per orphan/phantom
# FIXME: Test is slow as a turtle
# # TODO: make these tests extremely minimal. Test with 2-4 writes involved MAX. per orphan/phantom
# FIXME: Test is slow as a turtle
# # TODO: make these tests extremely minimal. Test with 2-4 writes involved MAX. per orphan/phantom
# FIXME: Test is slow as a turtle


@pytest.fixture(scope="function")
def test_power_events():
    """Define test shutdown and startup times for session integrity testing"""
    # Define timezone to ensure consistency
    tokyo_tz = pytz.timezone("Asia/Tokyo")

    test_time = tokyo_tz.localize(datetime(2025, 4, 15, 15, 15, 15))

    # Base time to work from (one day ago)
    base_time = test_time - timedelta(days=1)

    # System shutdown at 10 PM yesterday
    shutdown_time = base_time.replace(
        hour=22, minute=0, second=0, microsecond=0)

    # System startup at 8 AM today
    startup_time = base_time.replace(
        hour=8, minute=0, second=0, microsecond=0) + timedelta(days=1)

    return {
        "shutdown_time": shutdown_time,
        "startup_time": startup_time,
        "base_time": base_time
    }


@pytest_asyncio.fixture(scope="function")
async def test_program_logs(plain_asm, test_power_events):
    """Create test program summary logs with various scenarios"""
    events = test_power_events

    async with plain_asm() as session:
        shutdown_time = events["shutdown_time"]
        startup_time = events["startup_time"]
        base_time = events["base_time"]

        # Orphan type 1: started before shutdown, never ended
        # Removed: Cannot have a "Never ended" as end_time is not Nullable

        # orphan_1 = ProgramSummaryLog(
        #     program_name="Notepad",
        #     hours_spent=1.0,
        #     start_time=shutdown_time - timedelta(minutes=30),
        #     end_time=None,  # Never ended
        #     gathering_date=get_start_of_day_from_datetime(base_time),
        #     created_at=base_time
        # )
        # Orphan type 2: started before shutdown, ended after startup (impossible)
        orphan_2 = ProgramSummaryLog(
            exe_path_as_id="C:/ProgramFiles/Outlook.exe",
            process_name="Outlook.exe",
            program_name="Outlook",
            hours_spent=12.0,  # Impossibly long session
            start_time=shutdown_time - timedelta(minutes=45),
            start_time_local=shutdown_time.replace(
                tzinfo=None) - timedelta(minutes=45),
            end_time=startup_time + timedelta(minutes=15),
            end_time_local=startup_time.replace(
                tzinfo=None) + timedelta(minutes=15),
            gathering_date=get_start_of_day_from_datetime(base_time),
            gathering_date_local=get_start_of_day_from_datetime(
                base_time).replace(tzinfo=None),
            created_at=base_time
        )
        # Phantom: impossibly started during system off time
        phantom_1 = ProgramSummaryLog(
            exe_path_as_id="C:/ProgramFiles/Firefox.exe",
            process_name="Firefox.exe",
            program_name="Firefox",
            hours_spent=0.5,
            # Started after shutdown
            start_time=shutdown_time + timedelta(hours=2),
            # Ended before startup
            end_time=startup_time - timedelta(hours=2),
            start_time_local=shutdown_time.replace(tzinfo=None),
            end_time_local=startup_time.replace(tzinfo=None),
            gathering_date=get_start_of_day_from_datetime(base_time),
            gathering_date_local=get_start_of_day_from_datetime(
                base_time).replace(tzinfo=None),
            created_at=base_time
        )

        # Create test data
        program_logs = [
            # Normal session: started and ended before shutdown
            ProgramSummaryLog(
                exe_path_as_id="C:/ProgramFiles/PyCharm.exe",
                process_name="Pycharm.exe",
                program_name="PyCharm",
                hours_spent=2.0,
                start_time=shutdown_time - timedelta(hours=3),
                end_time=shutdown_time - timedelta(hours=1),
                start_time_local=shutdown_time.replace(
                    tzinfo=None) - timedelta(hours=3),
                end_time_local=shutdown_time.replace(
                    tzinfo=None) - timedelta(hours=1),
                gathering_date=get_start_of_day_from_datetime(base_time),
                gathering_date_local=get_start_of_day_from_datetime(
                    base_time).replace(tzinfo=None),
                created_at=base_time
            ),

            orphan_2,
            phantom_1,

            # Normal session after startup
            ProgramSummaryLog(
                exe_path_as_id="C:/ProgramFiles/Chrome.exe",
                process_name="Chrome.exe",
                program_name="Chrome",
                hours_spent=1.5,
                start_time=startup_time + timedelta(minutes=5),
                end_time=startup_time + timedelta(hours=1, minutes=35),
                start_time_local=startup_time.replace(tzinfo=None),
                end_time_local=startup_time.replace(
                    tzinfo=None) + timedelta(hours=1, minutes=35),
                gathering_date=get_start_of_day_from_datetime(
                    base_time + timedelta(days=1)),
                gathering_date_local=get_start_of_day_from_datetime(
                    base_time + timedelta(days=1)).replace(tzinfo=None),
                created_at=base_time + timedelta(days=1)
            )
        ]

        # Add all logs to the session
        for log in program_logs:
            session.add(log)

        await session.commit()

        return program_logs


@pytest_asyncio.fixture(scope="function")
async def test_domain_logs(plain_asm, test_power_events):
    """Create test domain summary logs with various scenarios"""
    events = test_power_events

    async with plain_asm() as session:
        shutdown_time = events["shutdown_time"]
        startup_time = events["startup_time"]
        base_time = events["base_time"]

        # Orphan type 1: started before shutdown, never ended
        # Removed: Cannot have a "Never ended" as end_time is not Nullable
        # orphan_1 = DomainSummaryLog(
        #     domain_name="stackoverflow.com",
        #     hours_spent=0.5,
        #     start_time=shutdown_time - timedelta(minutes=40),
        #     end_time=None,  # Never ended
        #     gathering_date=get_start_of_day_from_datetime(base_time),
        #     created_at=base_time
        # Orphan type 2: started before shutdown, ended after startup (impossible)
        # Orphan type 2: started before shutdown, ended after startup (impossible)
        orphan_2 = DomainSummaryLog(
            domain_name="youtube.com",
            hours_spent=10.0,  # Impossibly long session
            start_time=shutdown_time - timedelta(minutes=20),
            start_time_local=(
                shutdown_time - timedelta(minutes=20)).replace(tzinfo=None),
            end_time=startup_time + timedelta(minutes=10),
            end_time_local=(startup_time + timedelta(minutes=10)
                            ).replace(tzinfo=None),
            gathering_date=get_start_of_day_from_datetime(base_time),
            gathering_date_local=get_start_of_day_from_datetime(
                base_time).replace(tzinfo=None),
            created_at=base_time
        )
        # Phantom: impossibly started during system off time
        phantom_1 = DomainSummaryLog(
            domain_name="reddit.com",
            hours_spent=0.3,
            # Started after shutdown
            start_time=shutdown_time + timedelta(hours=3),
            start_time_local=(
                shutdown_time + timedelta(hours=3)).replace(tzinfo=None),
            # Ended before startup
            end_time=startup_time - timedelta(hours=1),
            end_time_local=(startup_time - timedelta(hours=1)
                            ).replace(tzinfo=None),
            gathering_date=get_start_of_day_from_datetime(base_time),
            gathering_date_local=get_start_of_day_from_datetime(
                base_time).replace(tzinfo=None),
            created_at=base_time
        )

        # Create test data
        domain_logs = [
            # Normal session: started and ended before shutdown
            DomainSummaryLog(
                domain_name="github.com",
                hours_spent=1.0,
                start_time=shutdown_time - timedelta(hours=2),
                start_time_local=(
                    shutdown_time - timedelta(hours=2)).replace(tzinfo=None),
                end_time=shutdown_time - timedelta(hours=1),
                end_time_local=(shutdown_time - timedelta(hours=1)
                                ).replace(tzinfo=None),
                gathering_date=get_start_of_day_from_datetime(base_time),
                gathering_date_local=get_start_of_day_from_datetime(
                    base_time).replace(tzinfo=None),
                created_at=base_time
            ),
            orphan_2,

            phantom_1,

            # Normal session after startup
            DomainSummaryLog(
                domain_name="google.com",
                hours_spent=0.8,
                start_time=startup_time + timedelta(minutes=10),
                start_time_local=(
                    startup_time + timedelta(minutes=10)).replace(tzinfo=None),
                end_time=startup_time + timedelta(minutes=58),
                end_time_local=(
                    startup_time + timedelta(minutes=58)).replace(tzinfo=None),
                gathering_date=get_start_of_day_from_datetime(
                    base_time + timedelta(days=1)),
                gathering_date_local=get_start_of_day_from_datetime(
                    base_time + timedelta(days=1)).replace(tzinfo=None),
                created_at=base_time + timedelta(days=1)
            )
        ]

        # Add all logs to the session
        for log in domain_logs:
            session.add(log)

        await session.commit()

        return domain_logs


@pytest_asyncio.fixture(scope="function")
def test_dao_instances(regular_session_maker, plain_asm):
    """Create the necessary DAO instances for session integrity testing"""
    # Create the DAOs
    program_logging_dao = ProgramLoggingDao(regular_session_maker)
    chrome_logging_dao = ChromeLoggingDao(regular_session_maker)

    # Create the session integrity dao
    session_integrity_dao = SessionIntegrityDao(
        program_logging_dao=program_logging_dao,
        chrome_logging_dao=chrome_logging_dao,
        session_maker=plain_asm
    )

    yield {
        "program_logging_dao": program_logging_dao,
        "chrome_logging_dao": chrome_logging_dao,
        "session_integrity_dao": session_integrity_dao
    }

    # session_integrity_dao.cleanup()


@pytest_asyncio.fixture(scope="function")
async def full_test_environment(
    sync_engine,
    test_power_events,
    test_program_logs,
    test_domain_logs,
    test_dao_instances
):
    """
    Combines all fixtures to provide a complete test environment
    """
    # Store the awaited engine, not the coroutine

    return {
        "engine": sync_engine,
        "power_events": test_power_events,
        "program_logs": test_program_logs,
        "domain_logs": test_domain_logs,
        "daos": test_dao_instances
    }
# Create a function that directly cleans up tables - this is simpler and more reliable


# Modify your test functions to call the cleanup explicitly
@pytest.mark.asyncio
async def test_find_orphans(full_test_environment):
    """Test that orphaned sessions are correctly identified"""
    env = full_test_environment

    # Get values from the environment
    engine = env["engine"]
    shutdown_time = env["power_events"]["shutdown_time"]
    startup_time = env["power_events"]["startup_time"]
    session_integrity_dao = env["daos"]["session_integrity_dao"]

    try:
        # Find orphans
        program_orphans, domain_orphans = session_integrity_dao.find_orphans(
            shutdown_time, startup_time
        )

        # Assertions
        assert isinstance(program_orphans, list)
        assert isinstance(domain_orphans, list)

        # Was 2 but one was removed because end_time is nonnullable
        assert len(program_orphans) == 1
        # Was 2 but one was removed because end_time is nonnullable
        assert len(domain_orphans) == 1
        assert any(log.program_name == "Outlook" for log in program_orphans)
        assert any(log.domain_name == "youtube.com" for log in domain_orphans)

    finally:
        # Clean up after test, regardless of whether it passed or failed
        truncate_logs_tables_via_engine(engine)


@pytest.mark.asyncio
async def test_find_phantoms(full_test_environment):
    """Test that phantom sessions are correctly identified"""
    env = full_test_environment

    # Get values from the environment
    engine = env["engine"]
    shutdown_time = env["power_events"]["shutdown_time"]
    startup_time = env["power_events"]["startup_time"]
    session_integrity_dao = env["daos"]["session_integrity_dao"]

    try:
        # Find phantoms
        program_phantoms, domain_phantoms = session_integrity_dao.find_phantoms(
            shutdown_time, startup_time
        )

        # Assertions
        assert len(program_phantoms) == 1
        assert len(domain_phantoms) == 1
        assert program_phantoms[0].program_name == "Firefox"
        assert domain_phantoms[0].domain_name == "reddit.com"

    finally:
        # Clean up after test, regardless of whether it passed or failed
        truncate_logs_tables_via_engine(engine)


# @pytest.mark.asyncio
# async def test_audit_sessions(full_test_environment):
#     """Test the complete audit_sessions method"""
#     env = full_test_environment

#     # Get values from the environment
#     engine = env["engine"]
#     shutdown_time = env["power_events"]["shutdown_time"]
#     startup_time = env["power_events"]["startup_time"]
#     session_integrity_dao = env["daos"]["session_integrity_dao"]

#     try:
#         # Run the full audit
#         await session_integrity_dao.audit_sessions(shutdown_time, startup_time)
#         # Test passes if no exceptions are raised

#     finally:
#         # Clean up after test, regardless of whether it passed or failed
#         await truncate_test_tables(engine)
