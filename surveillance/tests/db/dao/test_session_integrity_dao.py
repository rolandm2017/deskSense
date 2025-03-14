from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, MagicMock
import threading
import signal
import pytest


from src.db.dao.session_integrity_dao import SessionIntegrityDao
from src.db.dao.program_summary_dao import ProgramSummaryDao
from src.db.dao.summary_logs_dao import ProgramLoggingDao, ChromeLoggingDao
from src.db.models import DailyProgramSummary, DailyDomainSummary, ProgramSummaryLog, DomainSummaryLog

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import DailyProgramSummary, DailyDomainSummary, ProgramSummaryLog, DomainSummaryLog
from src.db.dao.program_summary_dao import ProgramSummaryDao
from src.db.dao.summary_logs_dao import ProgramLoggingDao, ChromeLoggingDao
from src.db.dao.session_integrity_dao import SessionIntegrityDao
from ...mocks.mock_clock import MockClock


@pytest.fixture(scope="function")
async def test_power_events():
    """Define test shutdown and startup times for session integrity testing"""
    # Define timezone to ensure consistency
    tz = timezone.utc

    # Base time to work from (one day ago)
    base_time = datetime.now(tz) - timedelta(days=1)

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


@pytest.fixture(scope="function")
async def test_program_logs(async_session_maker, test_power_events):
    """
    Create test program summary logs with various scenarios:
    - Normal sessions (start and end before shutdown)
    - Orphans (started before shutdown, no end or ended after startup)
    - Phantoms (started during system off time)
    """
    async with async_session_maker() as session:
        events = test_power_events
        shutdown_time = events["shutdown_time"]
        startup_time = events["startup_time"]
        base_time = events["base_time"]

        # Create test data
        program_logs = [
            # Normal session: started and ended before shutdown
            ProgramSummaryLog(
                program_name="VSCode",
                hours_spent=2.0,
                start_time=shutdown_time - timedelta(hours=3),
                end_time=shutdown_time - timedelta(hours=1),
                gathering_date=base_time.date(),
                created_at=base_time
            ),

            # Orphan type 1: started before shutdown, never ended
            ProgramSummaryLog(
                program_name="Notepad",
                hours_spent=1.0,
                start_time=shutdown_time - timedelta(minutes=30),
                end_time=None,  # Never ended
                gathering_date=base_time.date(),
                created_at=base_time
            ),

            # Orphan type 2: started before shutdown, ended after startup (impossible)
            ProgramSummaryLog(
                program_name="Outlook",
                hours_spent=12.0,  # Impossibly long session
                start_time=shutdown_time - timedelta(minutes=45),
                end_time=startup_time + timedelta(minutes=15),
                gathering_date=base_time.date(),
                created_at=base_time
            ),

            # Phantom: impossibly started during system off time
            ProgramSummaryLog(
                program_name="Firefox",
                hours_spent=0.5,
                # Started after shutdown
                start_time=shutdown_time + timedelta(hours=2),
                # Ended before startup
                end_time=startup_time - timedelta(hours=2),
                gathering_date=base_time.date(),
                created_at=base_time
            ),

            # Normal session after startup
            ProgramSummaryLog(
                program_name="Chrome",
                hours_spent=1.5,
                start_time=startup_time + timedelta(minutes=5),
                end_time=startup_time + timedelta(hours=1, minutes=35),
                gathering_date=(base_time + timedelta(days=1)).date(),
                created_at=base_time + timedelta(days=1)
            )
        ]

        # Add all logs to the session
        for log in program_logs:
            session.add(log)

        await session.commit()

        return program_logs


@pytest.fixture(scope="function")
async def test_domain_logs(async_session_maker, test_power_events):
    """
    Create test domain summary logs with various scenarios:
    - Normal sessions (start and end before shutdown)
    - Orphans (started before shutdown, no end or ended after startup)
    - Phantoms (started during system off time)
    """
    async with async_session_maker() as session:
        events = test_power_events
        shutdown_time = events["shutdown_time"]
        startup_time = events["startup_time"]
        base_time = events["base_time"]

        # Create test data
        domain_logs = [
            # Normal session: started and ended before shutdown
            DomainSummaryLog(
                domain_name="github.com",
                hours_spent=1.0,
                start_time=shutdown_time - timedelta(hours=2),
                end_time=shutdown_time - timedelta(hours=1),
                gathering_date=base_time.date(),
                created_at=base_time
            ),

            # Orphan type 1: started before shutdown, never ended
            DomainSummaryLog(
                domain_name="stackoverflow.com",
                hours_spent=0.5,
                start_time=shutdown_time - timedelta(minutes=40),
                end_time=None,  # Never ended
                gathering_date=base_time.date(),
                created_at=base_time
            ),

            # Orphan type 2: started before shutdown, ended after startup (impossible)
            DomainSummaryLog(
                domain_name="youtube.com",
                hours_spent=10.0,  # Impossibly long session
                start_time=shutdown_time - timedelta(minutes=20),
                end_time=startup_time + timedelta(minutes=10),
                gathering_date=base_time.date(),
                created_at=base_time
            ),

            # Phantom: impossibly started during system off time
            DomainSummaryLog(
                domain_name="reddit.com",
                hours_spent=0.3,
                # Started after shutdown
                start_time=shutdown_time + timedelta(hours=3),
                # Ended before startup
                end_time=startup_time - timedelta(hours=1),
                gathering_date=base_time.date(),
                created_at=base_time
            ),

            # Normal session after startup
            DomainSummaryLog(
                domain_name="google.com",
                hours_spent=0.8,
                start_time=startup_time + timedelta(minutes=10),
                end_time=startup_time + timedelta(minutes=58),
                gathering_date=(base_time + timedelta(days=1)).date(),
                created_at=base_time + timedelta(days=1)
            )
        ]

        # Add all logs to the session
        for log in domain_logs:
            session.add(log)

        await session.commit()

        return domain_logs


@pytest.fixture(scope="function")
async def test_dao_instances(async_session_maker):
    """
    Create the necessary DAO instances for session integrity testing
    """
    session_maker = async_session_maker

    # Create the DAOs
    program_logging_dao = ProgramLoggingDao(session_maker)
    chrome_logging_dao = ChromeLoggingDao(session_maker)

    # Create the session integrity dao
    session_integrity_dao = SessionIntegrityDao(
        program_logging_dao=program_logging_dao,
        chrome_logging_dao=chrome_logging_dao,
        session_maker=session_maker
    )

    return {
        "program_logging_dao": program_logging_dao,
        "chrome_logging_dao": chrome_logging_dao,
        "session_integrity_dao": session_integrity_dao
    }


@pytest.fixture(scope="function")
async def full_test_environment(
    async_session_maker,
    test_power_events,
    test_program_logs,
    test_domain_logs,
    test_dao_instances
):
    """
    Combines all fixtures to provide a complete test environment
    """
    return {
        "session_maker": async_session_maker,
        "power_events": test_power_events,
        "program_logs": test_program_logs,
        "domain_logs": test_domain_logs,
        "daos": test_dao_instances
    }


# Example test using the fixtures
async def test_find_orphans(full_test_environment):
    """Test that orphaned sessions are correctly identified"""
    env = full_test_environment
    shutdown_time = env["power_events"]["shutdown_time"]
    startup_time = env["power_events"]["startup_time"]

    # Get the session integrity DAO
    session_integrity_dao = env["daos"]["session_integrity_dao"]

    # Find orphans
    program_orphans, domain_orphans = await session_integrity_dao.find_orphans(
        shutdown_time, startup_time
    )

    # We should have 2 program orphans and 2 domain orphans
    assert len(program_orphans) == 2
    assert len(domain_orphans) == 2

    # Check the specific orphans we're expecting
    assert any(log.program_name == "Notepad" for log in program_orphans)
    assert any(log.program_name == "Outlook" for log in program_orphans)

    assert any(log.domain_name == "stackoverflow.com" for log in domain_orphans)
    assert any(log.domain_name == "youtube.com" for log in domain_orphans)


async def test_find_phantoms(full_test_environment):
    """Test that phantom sessions are correctly identified"""
    env = full_test_environment
    shutdown_time = env["power_events"]["shutdown_time"]
    startup_time = env["power_events"]["startup_time"]

    # Get the session integrity DAO
    session_integrity_dao = env["daos"]["session_integrity_dao"]

    # Find phantoms
    program_phantoms, domain_phantoms = await session_integrity_dao.find_phantoms(
        shutdown_time, startup_time
    )

    # We should have 1 program phantom and 1 domain phantom
    assert len(program_phantoms) == 1
    assert len(domain_phantoms) == 1

    # Check the specific phantoms we're expecting
    assert program_phantoms[0].program_name == "Firefox"
    assert domain_phantoms[0].domain_name == "reddit.com"


async def test_audit_sessions(full_test_environment):
    """Test the complete audit_sessions method"""
    env = full_test_environment
    shutdown_time = env["power_events"]["shutdown_time"]
    startup_time = env["power_events"]["startup_time"]

    # Get the session integrity DAO
    session_integrity_dao = env["daos"]["session_integrity_dao"]

    # Run the full audit
    await session_integrity_dao.audit_sessions(shutdown_time, startup_time)

    # Since we can't easily assert console output, this test mainly ensures
    # the method runs without errors. More detailed assertions are in the
    # specific orphan and phantom tests above.


def test_dao_finds_orphans():
    # TODO: Set up some orphans and non orphans
    shutdown_time = datetime.now()
    before_shutdown_1 = shutdown_time - timedelta(seconds=8)
    before_shutdown_2 = shutdown_time - timedelta(seconds=4)

    after_shutdown_1 = shutdown_time + timedelta(seconds=2)
    after_shutdown_2 = shutdown_time + timedelta(seconds=3)
    after_shutdown_3 = shutdown_time + timedelta(seconds=4)

    startup_time = after_shutdown_3 + timedelta(seconds=10)

    pass


def test_dao_finds_phantoms():
    shutdown_time = datetime.now()
    before_shutdown_1 = shutdown_time - timedelta(seconds=8)
    before_shutdown_2 = shutdown_time - timedelta(seconds=4)

    after_shutdown_1 = shutdown_time + timedelta(seconds=2)
    after_shutdown_2 = shutdown_time + timedelta(seconds=3)
    after_shutdown_3 = shutdown_time + timedelta(seconds=4)

    startup_time = after_shutdown_3 + timedelta(seconds=10)

    pass
    # TODO: Set up some phantoms and non-phantoms
