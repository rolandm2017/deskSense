
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock, MagicMock

from datetime import datetime, date, timedelta, timezone
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
import asyncio

from activitytracker.db.dao.direct.system_status_dao import SystemStatusDao
from activitytracker.db.models import SystemStatus, Base
from activitytracker.object.enums import SystemStatusType
from activitytracker.util.time_wrappers import UserLocalTime


from ....mocks.mock_clock import MockClock


import psutil

process = psutil.Process()
open_files = process.open_files()
num_open_files = len(open_files)
print(f"Num of open files: {num_open_files}")


@pytest_asyncio.fixture(scope="function")
async def test_db_dao(mock_regular_session_maker):
    """Create a DAO instance with the async session maker"""

    dt1 = datetime.now() - timedelta(seconds=20)
    dt2 = dt1 + timedelta(seconds=1)
    dt3 = dt1 + timedelta(seconds=2)
    dt4 = dt1 + timedelta(seconds=3)
    dt5 = dt1 + timedelta(seconds=4)
    times = [dt1, dt2, dt3, dt4, dt5]
    clock = MockClock(times)

    dao = SystemStatusDao(mock_regular_session_maker)

    current_loop = asyncio.get_event_loop()


@pytest.mark.asyncio
async def test_read_latest_status(test_db_dao):
    dao, clock = test_db_dao
    now = clock.now().replace(tzinfo=timezone.utc)

    pass


@pytest.mark.asyncio
async def test_read_latest_shutdown(test_db_dao):
    dao, clock = test_db_dao
    dt1 = clock.now().replace(tzinfo=timezone.utc)

    pass
