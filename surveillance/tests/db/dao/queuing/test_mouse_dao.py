import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock, patch
import asyncio

from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql.selectable import Select

from sqlalchemy import text

from typing import cast

from surveillance.src.db.dao.queuing.mouse_dao import MouseDao
from surveillance.src.db.models import MouseMove
from surveillance.src.object.classes import MouseMoveWindow
from surveillance.src.util.clock import SystemClock
from surveillance.src.util.time_wrappers import UserLocalTime


class TestMouseDao:
    @pytest_asyncio.fixture
    async def dao(self, mock_async_session_maker):

        print("Here, 40ruy")
        dao = MouseDao(mock_async_session_maker)
        yield dao
        # await truncate_table(asm)

    @pytest.mark.asyncio
    async def test_create_from_window(self, dao):
        start_time = UserLocalTime(datetime.now())
        end_time = start_time + timedelta(minutes=1)
        window = MouseMoveWindow(start_time, end_time)

        original_queue_item = dao.queue_item
        queue_item_spy = AsyncMock(side_effect=original_queue_item)
        dao.queue_item = queue_item_spy

        await dao.create_from_window(window)

        queue_item_spy.assert_called_once()

        queued_item = queue_item_spy.call_args[0][0]
        assert isinstance(queued_item, MouseMove)
        assert cast(datetime, queued_item.start_time) == start_time
        assert cast(datetime, queued_item.end_time) == end_time

    @pytest.mark.asyncio
    async def test_read_all(self, dao):
        # Test reading all moves

        t0 = datetime.now(timezone.utc)
        t1 = t0 - timedelta(seconds=10)
        t2 = t0 - timedelta(seconds=8)
        t3 = t0 - timedelta(seconds=6)

        pretend1 = MouseMove(id=300, start_time=t0, end_time=t1)
        pretend2 = MouseMove(id=301, start_time=t2, end_time=t3)

        execute_and_return_all_rows_mock = AsyncMock()
        execute_and_return_all_rows_mock.return_value = [pretend1, pretend2]
        dao.execute_and_return_all_rows = execute_and_return_all_rows_mock

        # Act
        result = await dao.read_all()

        # Assert
        execute_and_return_all_rows_mock.assert_called_once()
        args, _ = execute_and_return_all_rows_mock.call_args
        assert isinstance(args[0], Select)

        assert isinstance(result, list)
        assert len(result) == len([pretend1, pretend2])
        times = [result[0].start_time, result[1].start_time]
        assert t0 in times, "Window didn't come out of the db as expected"
        assert t2 in times, "Window didn't come out of the db as expected"

    @pytest.mark.asyncio
    async def test_read_past_24h_events(self, dao):
        t0 = datetime.now(timezone.utc)

        # Today:
        t1 = UserLocalTime(t0 - timedelta(seconds=10))
        t2 = UserLocalTime(t0 - timedelta(seconds=8))
        t3 = UserLocalTime(t0 - timedelta(seconds=6))
        test_1: MouseMoveWindow = MouseMoveWindow(
            start_of_window=t1, end_of_window=t2)
        test_2: MouseMoveWindow = MouseMoveWindow(
            start_of_window=t2, end_of_window=t3)

        todays_events = [test_1, test_2]

        get_prev_24_hrs_query_mock = Mock(
            side_effect=dao.get_prev_24_hours_query)
        dao.get_prev_24_hours_query = get_prev_24_hrs_query_mock

        exec_mock = AsyncMock()
        exec_mock.return_value = todays_events
        dao.execute_and_return_all_rows = exec_mock

        # # ### Act
        past_day = await dao.read_past_24h_events(UserLocalTime(t0))

        # # Assert
        exec_mock.assert_called_once()
        get_prev_24_hrs_query_mock.assert_called_once()

        assert len(past_day) == len(todays_events)

        args, _ = get_prev_24_hrs_query_mock.call_args
        assert isinstance(args[0], datetime)

        assert args[0].hour == t0.hour
        assert args[0].minute == t0.minute
        assert args[0].day + 1 == t0.day, "Wasn't one day later as expected"

        args, _ = exec_mock.call_args
        assert isinstance(args[0], Select)
