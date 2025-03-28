
import pytest
from unittest.mock import AsyncMock, Mock, MagicMock

from datetime import datetime, date, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text
import asyncio

import os
from dotenv import load_dotenv

from src.db.dao.system_status_dao import SystemStatusDao
from src.db.models import SystemStatus, Base
from src.object.enums import SystemStatusType

from ...mocks.mock_clock import MockClock

# FIXME: Tests are wayyyyyy too slow here 
# FIXME: Tests are wayyyyyy too slow here 
# FIXME: Tests are wayyyyyy too slow here 
# FIXME: Tests are wayyyyyy too slow here 
# FIXME: Tests are wayyyyyy too slow here 

# Load environment variables from .env file
load_dotenv()

# # Get the test database connection string
# ASYNC_TEST_DB_URL = os.getenv(
#     'ASYNC_TEST_DB_URL')







@pytest.fixture(scope="function")
async def test_db_dao(plain_async_engine_and_asm, shutdown_session_maker):
    """Create a DAO instance with the async session maker"""
    _, asm = plain_async_engine_and_asm

    dt1 = datetime.now() - timedelta(seconds=20)
    dt2 = dt1 + timedelta(seconds=1)
    dt3 = dt1 + timedelta(seconds=2)
    dt4 = dt1 + timedelta(seconds=3)
    dt5 = dt1 + timedelta(seconds=4)
    times = [dt1, dt2, dt3, dt4, dt5]
    clock = MockClock(times)

    dao = SystemStatusDao(asm, shutdown_session_maker)

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
    assert latest_shutdown is not None
    assert latest_shutdown.status == SystemStatusType.SLEEP
    print(latest_shutdown.created_at)
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
