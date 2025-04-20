
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock, MagicMock

from datetime import datetime, date, timedelta, timezone
from sqlalchemy import text
import asyncio

from surveillance.src.db.dao.direct.system_status_dao import SystemStatusDao
from surveillance.src.db.models import SystemStatus, Base
from surveillance.src.object.enums import SystemStatusType
from surveillance.src.util.time_wrappers import UserLocalTime


from ....mocks.mock_clock import MockClock


import psutil

process = psutil.Process()
open_files = process.open_files()
num_open_files = len(open_files)
print(f"Num of open files: {num_open_files}")


# FIXME: Tests are wayyyyyy too slow here

@pytest_asyncio.fixture(scope="function")
async def test_db_dao(async_engine_and_asm, regular_session):
    """Create a DAO instance with the async session maker"""
    _, asm = async_engine_and_asm

    dt1 = datetime.now() - timedelta(seconds=20)
    dt2 = dt1 + timedelta(seconds=1)
    dt3 = dt1 + timedelta(seconds=2)
    dt4 = dt1 + timedelta(seconds=3)
    dt5 = dt1 + timedelta(seconds=4)
    times = [dt1, dt2, dt3, dt4, dt5]
    clock = MockClock(times)

    dao = SystemStatusDao(asm, regular_session)

    current_loop = asyncio.get_event_loop()
    dao.accept_power_tracker_loop(current_loop)
    yield dao, clock
    await dao.async_session_maker().close()  # Close session explicitly


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db(test_db_dao):
    """Runs before each test automatically"""
    dao, clock = test_db_dao

    async with dao.async_session_maker() as session:
        await session.execute(text("TRUNCATE TABLE system_change_log RESTART IDENTITY CASCADE"))
        await session.commit()

    return dao, clock


@pytest.mark.asyncio
async def test_read_latest_status(setup_test_db):
    dao, clock = setup_test_db
    now = clock.now().replace(tzinfo=timezone.utc)

    # Test starting conditions:
    latest_shutdown = dao.read_latest_shutdown()
    assert latest_shutdown is None
    assert not hasattr(latest_shutdown, "status")

    # Arrange
    the_very_latest = SystemStatusType.CTRL_C_SIGNAL
    # Pretend this happened
    # await dao.create_status(SystemStatusType.STARTUP, now)
    # await dao.create_status(SystemStatusType.SHUTDOWN, now)
    # await dao.create_status(the_very_latest, now)

    read_latest_status_from_db_spy = Mock()
    pretend_return_val = SystemStatus()
    pretend_return_val.status = the_very_latest

    read_latest_status_from_db_spy.return_value = pretend_return_val
    dao.read_latest_status_from_db = read_latest_status_from_db_spy

    # Act
    latest_status = dao.read_latest_status()
    assert latest_status == the_very_latest


@pytest.mark.asyncio
async def test_create_different_statuses(setup_test_db):
    dao, clock = setup_test_db

    # Arrange
    write_sync_spy = Mock()
    write_sync_spy.return_value = True
    async_write_spy = AsyncMock()
    async_write_spy.return_value = True
    dao.write_sync = write_sync_spy
    dao.async_write = async_write_spy

    # Test regular async status creation
    now = UserLocalTime(clock.now().replace(tzinfo=timezone.utc))
    success = await dao.create_status(SystemStatusType.STARTUP, now)
    assert success is True
    async_write_spy.assert_called_once()
    args, kwargs = async_write_spy.call_args
    assert isinstance(args[0], SystemStatus)
    assert args[0].status == SystemStatusType.STARTUP
    async_write_spy.reset_mock()

    # Test critical status with sync write
    now = UserLocalTime(clock.now().replace(tzinfo=timezone.utc))
    success = await dao.create_status(SystemStatusType.SHUTDOWN, now)

    assert success is True
    write_sync_spy.assert_called_once()
    args, kwargs = write_sync_spy.call_args
    assert isinstance(args[0], SystemStatus)
    assert args[0].status == SystemStatusType.SHUTDOWN
    write_sync_spy.reset_mock()

    # Test emergency write
    now = UserLocalTime(clock.now().replace(tzinfo=timezone.utc))
    success = await dao.create_status(SystemStatusType.CTRL_C_SIGNAL, now)

    assert success is True
    write_sync_spy.assert_called_once()
    args, kwargs = write_sync_spy.call_args
    assert isinstance(args[0], SystemStatus)
    assert args[0].status == SystemStatusType.CTRL_C_SIGNAL


@pytest.mark.asyncio
async def test_read_latest_shutdown(setup_test_db):
    dao, clock = setup_test_db
    dt1 = clock.now().replace(tzinfo=timezone.utc)

    # # Test starting conditions:
    # latest_shutdown = dao.read_latest_shutdown()
    # assert latest_shutdown is None
    # assert not hasattr(latest_shutdown, "status")
    # assert latest_shutdown.status != SystemStatusType.SLEEP
    # assert latest_shutdown.status != SystemStatusType.SHUTDOWN
    # assert latest_shutdown.status != SystemStatusType.CTRL_C_SIGNAL

    # Test SLEEP
    read_latest_status_from_db_mock = Mock()
    sleep_status = SystemStatus()
    sleep_status.status = SystemStatusType.SLEEP
    read_latest_status_from_db_mock.return_value = sleep_status
    dao.read_latest_status_from_db = read_latest_status_from_db_mock
    # await dao.create_status(SystemStatusType.SLEEP, dt1)
    latest_shutdown = dao.read_latest_shutdown()
    assert latest_shutdown is not None
    assert latest_shutdown.status == SystemStatusType.SLEEP

    # Test SHUTDOWN
    dt2 = dt1 + timedelta(seconds=2)
    read_latest_status_from_db_mock = Mock()
    shutdown_status = SystemStatus()
    shutdown_status.status = SystemStatusType.SHUTDOWN
    read_latest_status_from_db_mock.return_value = shutdown_status
    dao.read_latest_status_from_db = read_latest_status_from_db_mock
    # await dao.create_status(SystemStatusType.SHUTDOWN, dt2)
    latest_shutdown = dao.read_latest_shutdown()
    assert latest_shutdown is not None
    assert latest_shutdown.status == SystemStatusType.SHUTDOWN

    # Test CTRL C
    read_latest_status_from_db_mock = Mock()
    ctrl_c_status = SystemStatus()
    ctrl_c_status.status = SystemStatusType.CTRL_C_SIGNAL
    read_latest_status_from_db_mock.return_value = ctrl_c_status
    dao.read_latest_status_from_db = read_latest_status_from_db_mock
    # await dao.create_status(SystemStatusType.CTRL_C_SIGNAL, dt3)
    latest_shutdown = dao.read_latest_shutdown()
    assert latest_shutdown is not None
    assert latest_shutdown.status == SystemStatusType.CTRL_C_SIGNAL

    # Test HOT RELOAD
    read_latest_status_from_db_mock = Mock()
    hot_reload_status = SystemStatus()
    hot_reload_status.status = SystemStatusType.HOT_RELOAD_STARTED
    read_latest_status_from_db_mock.return_value = hot_reload_status
    dao.read_latest_status_from_db = read_latest_status_from_db_mock
    # await dao.create_status(SystemStatusType.HOT_RELOAD_STARTED, dt4)
    latest_shutdown = dao.read_latest_shutdown()
    assert latest_shutdown is not None
    assert latest_shutdown.status == SystemStatusType.HOT_RELOAD_STARTED


@pytest.mark.asyncio
async def test_read_latest_status_returns_none_if_no_statuses(setup_test_db):
    dao, clock = setup_test_db

    read_latest_status_from_db_mock = Mock()
    read_latest_status_from_db_mock.return_value = None
    dao.read_latest_status_from_db = read_latest_status_from_db_mock

    latest_status = dao.read_latest_status()
    assert latest_status is None
    assert not hasattr(latest_status, "status")


@pytest.mark.asyncio
async def test_read_latest_shutdown_returns_none_if_no_statuses(setup_test_db):
    dao, clock = setup_test_db

    read_latest_status_from_db_mock = Mock()
    read_latest_status_from_db_mock.return_value = None
    dao.read_latest_status_from_db = read_latest_status_from_db_mock

    latest_shutdown = dao.read_latest_shutdown()
    assert latest_shutdown is None
    assert not hasattr(latest_shutdown, "status")
