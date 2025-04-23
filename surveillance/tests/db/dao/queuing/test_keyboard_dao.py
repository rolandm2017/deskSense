import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, patch, Mock, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import text

from surveillance.src.object.dto import TypingSessionDto
from surveillance.src.db.dao.queuing.keyboard_dao import KeyboardDao
from surveillance.src.db.models import TypingSession
from surveillance.src.object.classes import KeyboardAggregate
from surveillance.src.util.clock import SystemClock
from surveillance.src.util.time_wrappers import UserLocalTime


@pytest_asyncio.fixture
async def dao(mock_async_session_maker):
    dao = KeyboardDao(mock_async_session_maker)
    yield dao


@pytest.mark.asyncio
async def test_create(dao):
    # Arrange
    session = KeyboardAggregate(
        start_time=UserLocalTime(datetime.now()),
        end_time=UserLocalTime(datetime.now())
    )

    queue_item_mock = AsyncMock()
    dao.queue_item = queue_item_mock

    # Act
    await dao.create(session)

    # Assert
    queue_item_mock.assert_called_once()

    args, _ = queue_item_mock.call_args
    assert isinstance(args[0], TypingSession)


@pytest.mark.asyncio
async def test_read_all(dao):

    # Write two dummy results
    s = TypingSession(id=4999,
                      start_time=datetime.now(),
                      end_time=datetime.now()
                      )
    s2 = TypingSession(id=5000,
                       start_time=datetime.now(),
                       end_time=datetime.now()
                       )
    execute_and_return_all_mock = AsyncMock()
    execute_and_return_all_mock.return_value = [s, s2]
    dao.execute_and_return_all_rows = execute_and_return_all_mock

    # Act
    result = await dao.read_all()

    # Assert
    assert len(result) == 2
    assert all(isinstance(r, TypingSessionDto) for r in result)
    assert [r.id for r in result] == [4999, 5000]


@pytest.mark.asyncio
async def test_read_past_24h_events(dao):
    # Arrange
    current_time = UserLocalTime(datetime.now())

    s = TypingSession(id=5999,
                      start_time=datetime.now(),
                      end_time=datetime.now()
                      )
    s2 = TypingSession(id=6000,
                       start_time=datetime.now(),
                       end_time=datetime.now()
                       )
    execute_and_return_all_mock = AsyncMock()
    execute_and_return_all_mock.return_value = [s, s2]
    dao.execute_and_return_all_rows = execute_and_return_all_mock

    # Act
    result = await dao.read_past_24h_events(current_time)

    # Assert
    assert len(result) == 2
    assert all(isinstance(r, TypingSessionDto) for r in result)
    assert result[0].id == 5999
    assert result[1].id == 6000
