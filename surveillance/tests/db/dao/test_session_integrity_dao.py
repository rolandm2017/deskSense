import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select, text, func

from dotenv import load_dotenv
import os

# Import models and DAOs
from src.db.models import Base, SystemStatus, ProgramSummaryLog, DomainSummaryLog
from src.db.dao.session_integrity_dao import SessionIntegrityDao
from src.db.dao.program_logs_dao import ProgramLoggingDao
from src.db.dao.chrome_logs_dao import ChromeLoggingDao

# Load environment variables from .env file
load_dotenv()

# Get the test database connection string
ASYNC_TEST_DB_URL = os.getenv('ASYNC_TEST_DB_URL')
SYNC_TEST_DB_URL = os.getenv("SYNC_TEST_DB_URL")

if ASYNC_TEST_DB_URL is None:
    raise ValueError("ASYNC_TEST_DB_URL environment variable is not set")

if SYNC_TEST_DB_URL is None:
    raise ValueError("SYNC_TEST_DB_URL environment variable is not set")


@pytest_asyncio.fixture(scope="function")
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
        isolation_level="AUTOCOMMIT"
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


@pytest_asyncio.fixture(scope="function")
async def async_session_maker(async_engine):
    """Create an async session maker"""
    # Instead of anext(), just use async_engine directly since we've fixed the yield
    session_maker = async_sessionmaker(
        bind=async_engine,
        expire_on_commit=False
    )
    return session_maker


@pytest_asyncio.fixture(scope="function")
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


@pytest_asyncio.fixture(scope="function")
async def test_program_logs(async_session_maker, test_power_events):
    """Create test program summary logs with various scenarios"""
    events = test_power_events

    async with async_session_maker() as session:
        shutdown_time = events["shutdown_time"]
        startup_time = events["startup_time"]
        base_time = events["base_time"]

        # Orphan type 1: started before shutdown, never ended
        orphan_1 = ProgramSummaryLog(
            program_name="Notepad",
            hours_spent=1.0,
            start_time=shutdown_time - timedelta(minutes=30),
            end_time=None,  # Never ended
            gathering_date=base_time.date(),
            created_at=base_time
        )
        # Orphan type 2: started before shutdown, ended after startup (impossible)
        orphan_2 = ProgramSummaryLog(
            program_name="Outlook",
            hours_spent=12.0,  # Impossibly long session
            start_time=shutdown_time - timedelta(minutes=45),
            end_time=startup_time + timedelta(minutes=15),
            gathering_date=base_time.date(),
            created_at=base_time
        )
        # Phantom: impossibly started during system off time
        phantom_1 = ProgramSummaryLog(
            program_name="Firefox",
            hours_spent=0.5,
            # Started after shutdown
            start_time=shutdown_time + timedelta(hours=2),
            # Ended before startup
            end_time=startup_time - timedelta(hours=2),
            gathering_date=base_time.date(),
            created_at=base_time
        )

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
            orphan_1,
            orphan_2,
            phantom_1,

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


@pytest_asyncio.fixture(scope="function")
async def test_domain_logs(async_session_maker, test_power_events):
    """Create test domain summary logs with various scenarios"""
    events = test_power_events

    async with async_session_maker() as session:
        shutdown_time = events["shutdown_time"]
        startup_time = events["startup_time"]
        base_time = events["base_time"]

        # Orphan type 1: started before shutdown, never ended
        orphan_1 = DomainSummaryLog(
            domain_name="stackoverflow.com",
            hours_spent=0.5,
            start_time=shutdown_time - timedelta(minutes=40),
            end_time=None,  # Never ended
            gathering_date=base_time.date(),
            created_at=base_time
        )
        # Orphan type 2: started before shutdown, ended after startup (impossible)
        orphan_2 = DomainSummaryLog(
            domain_name="youtube.com",
            hours_spent=10.0,  # Impossibly long session
            start_time=shutdown_time - timedelta(minutes=20),
            end_time=startup_time + timedelta(minutes=10),
            gathering_date=base_time.date(),
            created_at=base_time
        )
        # Phantom: impossibly started during system off time
        phantom_1 = DomainSummaryLog(
            domain_name="reddit.com",
            hours_spent=0.3,
            # Started after shutdown
            start_time=shutdown_time + timedelta(hours=3),
            # Ended before startup
            end_time=startup_time - timedelta(hours=1),
            gathering_date=base_time.date(),
            created_at=base_time
        )

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
            orphan_1,
            orphan_2,

            phantom_1,

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


@pytest_asyncio.fixture(scope="function")
async def test_dao_instances(async_session_maker):
    """Create the necessary DAO instances for session integrity testing"""
    # Create the DAOs
    program_logging_dao = ProgramLoggingDao(async_session_maker)
    chrome_logging_dao = ChromeLoggingDao(async_session_maker)

    # Create the session integrity dao
    session_integrity_dao = SessionIntegrityDao(
        program_logging_dao=program_logging_dao,
        chrome_logging_dao=chrome_logging_dao,
        session_maker=async_session_maker
    )

    return {
        "program_logging_dao": program_logging_dao,
        "chrome_logging_dao": chrome_logging_dao,
        "session_integrity_dao": session_integrity_dao
    }


@pytest_asyncio.fixture(scope="function")
async def full_test_environment(
    async_engine,
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
        "engine": async_engine,
        "session_maker": async_session_maker,
        "power_events": test_power_events,
        "program_logs": test_program_logs,
        "domain_logs": test_domain_logs,
        "daos": test_dao_instances
    }
# Create a function that directly cleans up tables - this is simpler and more reliable


async def truncate_test_tables(engine):
    """Truncate all test tables directly"""
    # NOTE: IF you run the tests in a broken manner,
    # ####  the first run AFTER fixing the break
    # ####  MAY still look broken.
    # ####  Because the truncation happens *at the end of* a test.

    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE program_summary_logs RESTART IDENTITY CASCADE"))
        await conn.execute(text("TRUNCATE domain_summary_logs RESTART IDENTITY CASCADE"))
        await conn.execute(text("TRUNCATE system_change_log RESTART IDENTITY CASCADE"))
        print("Tables truncated")


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
        program_orphans, domain_orphans = await session_integrity_dao.find_orphans(
            shutdown_time, startup_time
        )

        # Assertions
        assert len(program_orphans) == 2
        assert len(domain_orphans) == 2
        assert any(log.program_name == "Notepad" for log in program_orphans)
        assert any(log.program_name == "Outlook" for log in program_orphans)
        assert any(log.domain_name ==
                   "stackoverflow.com" for log in domain_orphans)
        assert any(log.domain_name == "youtube.com" for log in domain_orphans)

    finally:
        # Clean up after test, regardless of whether it passed or failed
        await truncate_test_tables(engine)


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
        program_phantoms, domain_phantoms = await session_integrity_dao.find_phantoms(
            shutdown_time, startup_time
        )

        # Assertions
        assert len(program_phantoms) == 1
        assert len(domain_phantoms) == 1
        assert program_phantoms[0].program_name == "Firefox"
        assert domain_phantoms[0].domain_name == "reddit.com"

    finally:
        # Clean up after test, regardless of whether it passed or failed
        await truncate_test_tables(engine)


@pytest.mark.asyncio
async def test_audit_sessions(full_test_environment):
    """Test the complete audit_sessions method"""
    env = full_test_environment

    # Get values from the environment
    engine = env["engine"]
    shutdown_time = env["power_events"]["shutdown_time"]
    startup_time = env["power_events"]["startup_time"]
    session_integrity_dao = env["daos"]["session_integrity_dao"]

    try:
        # Run the full audit
        await session_integrity_dao.audit_sessions(shutdown_time, startup_time)
        # Test passes if no exceptions are raised

    finally:
        # Clean up after test, regardless of whether it passed or failed
        await truncate_test_tables(engine)
