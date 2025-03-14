from gc import set_debug
import pytest
from unittest.mock import AsyncMock, Mock, MagicMock
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text
import asyncio


from dotenv import load_dotenv
import os

from src.db.dao.system_status_dao import SystemStatusDao
from src.db.models import SystemStatus, Base
from src.object.enums import SystemStatusType

from ...mocks.mock_clock import MockClock

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
def sync_engine():
    """Create a synchronous PostgreSQL engine for testing"""
    # Create engine that connects to default postgres database
    if SYNC_TEST_DB_URL is None:
        raise ValueError("SYNC_TEST_DB_URL was None")

    from sqlalchemy import create_engine, text

    # Extract the default postgres database URL
    default_url = SYNC_TEST_DB_URL.rsplit('/', 1)[0] + '/postgres'
    admin_engine = create_engine(
        default_url,
        isolation_level="AUTOCOMMIT"
    )

    with admin_engine.connect() as conn:
        # Terminate existing connections more safely
        conn.execute(text("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = 'dsTestDb'
            AND pid <> pg_backend_pid()
        """))

        # Drop and recreate database
        conn.execute(text("DROP DATABASE IF EXISTS dsTestDb"))
        conn.execute(text("CREATE DATABASE dsTestDb"))

    admin_engine.dispose()

    # Create engine for test database
    test_engine = create_engine(
        # pool_pre_ping resolves a bug
        SYNC_TEST_DB_URL, isolation_level="AUTOCOMMIT", pool_pre_ping=True)

    # Create all tables
    with test_engine.begin() as conn:
        Base.metadata.create_all(conn)

    try:
        yield test_engine
    finally:
        test_engine.dispose()

        # Clean up by dropping test database
        admin_engine = create_engine(
            default_url,
            isolation_level="AUTOCOMMIT"
        )
        with admin_engine.connect() as conn:
            conn.execute(text("""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = 'dsTestDb'
                AND pid <> pg_backend_pid()
            """))
            conn.execute(text("DROP DATABASE IF EXISTS dsTestDb"))
        admin_engine.dispose()


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


@pytest.fixture(scope="function")
def shutdown_session_maker(sync_engine):
    """Create a synchronous session maker"""
    from sqlalchemy.orm import sessionmaker

    session_maker = sessionmaker(
        sync_engine,
        expire_on_commit=False
    )

    # session_factory = sessionmaker(bind=sync_engine, expire_on_commit=False)

    # shutdown_session_maker = scoped_session(session_factory)
    return session_maker


@pytest.fixture(scope="function")
async def test_db_dao(async_session_maker, shutdown_session_maker):
    """Create a DAO instance with the async session maker"""
    session_maker_async = await async_session_maker

    dt1 = datetime.now() - timedelta(seconds=20)
    dt2 = dt1 + timedelta(seconds=1)
    dt3 = dt1 + timedelta(seconds=2)
    dt4 = dt1 + timedelta(seconds=3)
    dt5 = dt1 + timedelta(seconds=4)
    times = [dt1, dt2, dt3, dt4, dt5]
    clock = MockClock(times)

    dao = SystemStatusDao(session_maker_async, shutdown_session_maker)

    current_loop = asyncio.get_event_loop()
    dao.accept_power_tracker_loop(current_loop)
    return dao, clock


@pytest.fixture(autouse=True)
async def setup_test_db(test_db_dao):
    """Runs before each test automatically"""
    dao, clock = await test_db_dao

    async with dao.async_session_maker() as session:
        await session.execute(text("TRUNCATE TABLE system_change_log RESTART IDENTITY CASCADE"))
        await session.commit()

    return dao, clock


@pytest.mark.asyncio
async def test_read_latest_status(setup_test_db):
    dao, clock = await setup_test_db
    now = clock.now().replace(tzinfo=timezone.utc)

    # Test starting conditions:
    latest_shutdown = await dao.read_latest_shutdown()
    assert latest_shutdown is None
    assert not hasattr(latest_shutdown, "status")

    # Arrange
    await dao.create_status(SystemStatusType.STARTUP, now)
    await dao.create_status(SystemStatusType.SHUTDOWN, now)
    the_very_latest = SystemStatusType.CTRL_C_SIGNAL
    await dao.create_status(the_very_latest, now)

    # Act
    latest_status = await dao.read_latest_status()
    assert latest_status == the_very_latest


@pytest.mark.asyncio
async def test_create_different_statuses(setup_test_db):
    dao, clock = await setup_test_db
    now = clock.now().replace(tzinfo=timezone.utc)

    # Test starting conditions:
    latest_shutdown = await dao.read_latest_shutdown()
    assert latest_shutdown is None
    assert not hasattr(latest_shutdown, "status")

    # Test regular async status creation
    success = await dao.create_status(SystemStatusType.STARTUP, now)
    assert success is True

    # Read back the status
    latest_status = await dao.read_latest_status()
    assert latest_status == SystemStatusType.STARTUP

    # Test critical status with sync write
    now = clock.now().replace(tzinfo=timezone.utc)  # Get next time
    success = await dao.create_status(SystemStatusType.SHUTDOWN, now)
    assert success is True

    # Read back the status
    latest_status = await dao.read_latest_status()
    assert latest_status == SystemStatusType.SHUTDOWN

    # Test emergency write
    now = clock.now().replace(tzinfo=timezone.utc)  # Get next time
    success = await dao.create_status(SystemStatusType.CTRL_C_SIGNAL, now)
    assert success is True

    # Read back the status
    latest_status = await dao.read_latest_status()
    assert latest_status == SystemStatusType.CTRL_C_SIGNAL


@pytest.mark.asyncio
async def test_read_latest_shutdown(setup_test_db):
    dao, clock = await setup_test_db
    dt1 = clock.now().replace(tzinfo=timezone.utc)

    # Test starting conditions:
    latest_shutdown = await dao.read_latest_shutdown()
    assert latest_shutdown is None
    assert not hasattr(latest_shutdown, "status")
    # assert latest_shutdown.status != SystemStatusType.SLEEP
    # assert latest_shutdown.status != SystemStatusType.SHUTDOWN
    # assert latest_shutdown.status != SystemStatusType.CTRL_C_SIGNAL

    # Test SLEEP
    await dao.create_status(SystemStatusType.SLEEP, dt1)
    print("dt1: ", dt1)
    latest_shutdown = await dao.read_latest_shutdown()
    print("dt?:", latest_shutdown.created_at, "290ru")
    assert latest_shutdown is not None
    assert latest_shutdown.status == SystemStatusType.SLEEP
    print(latest_shutdown.created_at)
    print(dt1, "292ru")
    assert latest_shutdown.created_at == dt1

    # Test SHUTDOWN
    dt2 = dt1 + timedelta(seconds=2)  # Get next time
    await dao.create_status(SystemStatusType.SHUTDOWN, dt2)
    latest_shutdown = await dao.read_latest_shutdown()
    assert latest_shutdown is not None
    assert latest_shutdown.status == SystemStatusType.SHUTDOWN
    assert latest_shutdown.created_at == dt2

    # Test CTRL C
    dt3 = dt1 + timedelta(seconds=4)  # Get next time
    await dao.create_status(SystemStatusType.CTRL_C_SIGNAL, dt3)
    latest_shutdown = await dao.read_latest_shutdown()
    assert latest_shutdown is not None
    assert latest_shutdown.status == SystemStatusType.CTRL_C_SIGNAL
    assert latest_shutdown.created_at == dt3

    # Test HOT RELOAD
    dt4 = dt1 + timedelta(seconds=7)  # Get next time
    await dao.create_status(SystemStatusType.HOT_RELOAD_STARTED, dt4)
    latest_shutdown = await dao.read_latest_shutdown()
    assert latest_shutdown is not None
    assert latest_shutdown.status == SystemStatusType.HOT_RELOAD_STARTED
    assert latest_shutdown.created_at == dt4


@pytest.mark.asyncio
async def test_read_latest_status_returns_none_if_no_statuses(setup_test_db):
    dao, clock = await setup_test_db

    latest_status = await dao.read_latest_status()
    assert latest_status is None
    assert not hasattr(latest_status, "status")


@pytest.mark.asyncio
async def test_read_latest_shutdown_returns_none_if_no_statuses(setup_test_db):
    dao, clock = await setup_test_db

    latest_shutdown = await dao.read_latest_shutdown()
    assert latest_shutdown is None
    assert not hasattr(latest_shutdown, "status")
