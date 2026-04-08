import pytest

import pytz
from datetime import datetime, timedelta
from unittest.mock import Mock
from sqlalchemy.orm import sessionmaker

from dotenv import load_dotenv
import os

from activitytracker.db.models import ProgramActivityLog, DomainActivityLog
from activitytracker.db.dao.direct.session_integrity_dao import SessionIntegrityDao
from activitytracker.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from activitytracker.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from activitytracker.tz_handling.time_formatting import get_start_of_day_from_datetime

from ....helper.truncation import truncate_logs_tables_via_engine

# Load environment variables from .env file
load_dotenv()

SYNC_TEST_DB_URL = os.getenv("SYNC_TEST_DB_URL")

if SYNC_TEST_DB_URL is None:
    raise ValueError("SYNC_TEST_DB_URL environment variable is not set")

pytestmark = pytest.mark.postgres_contract

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
    shutdown_time = base_time.replace(hour=22, minute=0, second=0, microsecond=0)

    # System startup at 8 AM today
    startup_time = base_time.replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(
        days=1
    )

    return {
        "shutdown_time": shutdown_time,
        "startup_time": startup_time,
        "base_time": base_time,
    }


def build_program_log(name, process_name, exe_path, start_time, end_time, gathering_date):
    return ProgramActivityLog(
        exe_path_as_id=exe_path,
        process_name=process_name,
        program_name=name,
        hours_spent=abs((end_time - start_time).total_seconds()) / 3600,
        start_time=start_time,
        end_time=end_time,
        start_time_local=start_time.replace(tzinfo=None),
        end_time_local=end_time.replace(tzinfo=None),
        gathering_date=gathering_date,
        gathering_date_local=gathering_date.replace(tzinfo=None),
        created_at=start_time,
    )


def build_domain_log(domain_name, start_time, end_time, gathering_date):
    return DomainActivityLog(
        domain_name=domain_name,
        hours_spent=abs((end_time - start_time).total_seconds()) / 3600,
        start_time=start_time,
        end_time=end_time,
        start_time_local=start_time.replace(tzinfo=None),
        end_time_local=end_time.replace(tzinfo=None),
        gathering_date=gathering_date,
        gathering_date_local=gathering_date.replace(tzinfo=None),
        created_at=start_time,
    )


@pytest.fixture(scope="function")
def session_integrity_session_maker(sync_engine):
    truncate_logs_tables_via_engine(sync_engine)
    maker = sessionmaker(sync_engine, expire_on_commit=False)
    yield maker


@pytest.fixture(scope="function")
def session_integrity_dao(session_integrity_session_maker):
    program_logging_dao = ProgramLoggingDao(session_integrity_session_maker)
    chrome_logging_dao = ChromeLoggingDao(session_integrity_session_maker)
    return SessionIntegrityDao(
        program_logging_dao=program_logging_dao,
        chrome_logging_dao=chrome_logging_dao,
        session_maker=Mock(),
    )


@pytest.fixture(scope="function")
def orphan_dataset(session_integrity_session_maker, test_power_events):
    events = test_power_events
    shutdown_time = events["shutdown_time"]
    startup_time = events["startup_time"]
    base_time = events["base_time"]
    gathering_date = get_start_of_day_from_datetime(base_time)

    with session_integrity_session_maker() as session:
        session.add(
            build_program_log(
                "PyCharm",
                "Pycharm.exe",
                "C:/ProgramFiles/PyCharm.exe",
                shutdown_time - timedelta(hours=2),
                shutdown_time - timedelta(hours=1),
                gathering_date,
            )
        )
        session.add(
            build_program_log(
                "Outlook",
                "Outlook.exe",
                "C:/ProgramFiles/Outlook.exe",
                shutdown_time - timedelta(minutes=45),
                startup_time + timedelta(minutes=15),
                gathering_date,
            )
        )
        session.add(
            build_domain_log(
                "github.com",
                shutdown_time - timedelta(hours=2),
                shutdown_time - timedelta(hours=1),
                gathering_date,
            )
        )
        session.add(
            build_domain_log(
                "youtube.com",
                shutdown_time - timedelta(minutes=20),
                startup_time + timedelta(minutes=10),
                gathering_date,
            )
        )
        session.commit()


@pytest.fixture(scope="function")
def phantom_dataset(session_integrity_session_maker, test_power_events):
    events = test_power_events
    shutdown_time = events["shutdown_time"]
    startup_time = events["startup_time"]
    base_time = events["base_time"]
    gathering_date = get_start_of_day_from_datetime(base_time)

    with session_integrity_session_maker() as session:
        session.add(
            build_program_log(
                "Chrome",
                "Chrome.exe",
                "C:/ProgramFiles/Chrome.exe",
                startup_time + timedelta(minutes=5),
                startup_time + timedelta(minutes=35),
                gathering_date,
            )
        )
        session.add(
            build_program_log(
                "Firefox",
                "Firefox.exe",
                "C:/ProgramFiles/Firefox.exe",
                shutdown_time + timedelta(hours=2),
                startup_time - timedelta(hours=2),
                gathering_date,
            )
        )
        session.add(
            build_domain_log(
                "google.com",
                startup_time + timedelta(minutes=10),
                startup_time + timedelta(minutes=58),
                gathering_date,
            )
        )
        session.add(
            build_domain_log(
                "reddit.com",
                shutdown_time + timedelta(hours=3),
                startup_time - timedelta(hours=1),
                gathering_date,
            )
        )
        session.commit()


# Create a function that directly cleans up tables - this is simpler and more reliable


# Modify your test functions to call the cleanup explicitly
def test_find_orphans(test_power_events, orphan_dataset, session_integrity_dao):
    """Test that orphaned sessions are correctly identified"""
    shutdown_time = test_power_events["shutdown_time"]
    startup_time = test_power_events["startup_time"]

    program_orphans, domain_orphans = session_integrity_dao.find_orphans(
        shutdown_time, startup_time
    )

    assert isinstance(program_orphans, list)
    assert isinstance(domain_orphans, list)
    assert len(program_orphans) == 1
    assert len(domain_orphans) == 1
    assert any(log.program_name == "Outlook" for log in program_orphans)
    assert any(log.domain_name == "youtube.com" for log in domain_orphans)


def test_find_phantoms(test_power_events, phantom_dataset, session_integrity_dao):
    """Test that phantom sessions are correctly identified"""
    shutdown_time = test_power_events["shutdown_time"]
    startup_time = test_power_events["startup_time"]

    program_phantoms, domain_phantoms = session_integrity_dao.find_phantoms(
        shutdown_time, startup_time
    )

    assert len(program_phantoms) == 1
    assert len(domain_phantoms) == 1
    assert program_phantoms[0].program_name == "Firefox"
    assert domain_phantoms[0].domain_name == "reddit.com"


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
