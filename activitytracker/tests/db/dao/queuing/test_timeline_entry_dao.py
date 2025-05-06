import pytest
from unittest.mock import AsyncMock, Mock, MagicMock, patch

from datetime import datetime, timedelta
import pytz

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.sql.selectable import Select
from typing import cast

from activitytracker.db.dao.queuing.timeline_entry_dao import TimelineEntryDao
from activitytracker.db.models import TimelineEntryObj
from activitytracker.object.classes import KeyboardAggregate, MouseMoveWindow
from activitytracker.object.enums import ChartEventType
from activitytracker.util.clock import SystemClock
from activitytracker.util.time_wrappers import UserLocalTime

import psutil


tokyo_tz = pytz.timezone("Asia/Tokyo")

test_time = tokyo_tz.localize(datetime(2025, 4, 25, 12, 12, 12))


# FIXME: OSerror


class TestTimelineEntryDao:
    @pytest.fixture
    def dao(self, mock_regular_session_maker):
        return TimelineEntryDao(mock_regular_session_maker)

    @pytest.mark.asyncio
    async def test_create_from_keyboard_aggregate(self, dao, mock_session):
        # Arrange
        current_time = test_time
        keyboard_aggregate = KeyboardAggregate(
            start_time=UserLocalTime(current_time),
            end_time=UserLocalTime(current_time + timedelta(minutes=5))
        )

        # Mock highest_id query
        mock_result = AsyncMock()
        mock_result.scalar = Mock(return_value=5)  # No need for AsyncMock here
        mock_session.execute.return_value = mock_result

        dao.queue_item = AsyncMock()

        # Act
        await dao.create_from_keyboard_aggregate(keyboard_aggregate)

        # Assert
        assert dao.queue_item.called
        queued_item = dao.queue_item.call_args[0][0]
        assert isinstance(queued_item, TimelineEntryObj)
        assert cast(str, queued_item.group) == ChartEventType.KEYBOARD

    @pytest.mark.asyncio
    async def test_create_from_mouse_move_window(self, dao, mock_session):
        # Arrange
        current_time = test_time
        mouse_window = MouseMoveWindow(
            UserLocalTime(current_time), UserLocalTime(current_time + timedelta(minutes=5)))

        # Mock highest_id query
        mock_result = AsyncMock()
        mock_result.scalar = Mock(return_value=5)
        mock_session.execute.return_value = mock_result

        dao.queue_item = AsyncMock()

        # Act
        await dao.create_from_mouse_move_window(mouse_window)

        # Assert
        assert dao.queue_item.called
        queued_item = dao.queue_item.call_args[0][0]
        assert isinstance(queued_item, TimelineEntryObj)
        assert cast(str, queued_item.group) == ChartEventType.MOUSE

    @pytest.mark.asyncio
    async def test_read_day(self, dao, mock_session):
        # Arrange
        test_day = UserLocalTime(test_time)
        event_type = ChartEventType.KEYBOARD
        mock_entries = [
            Mock(spec=TimelineEntryObj),
            Mock(spec=TimelineEntryObj)
        ]

        get_find_by_day_mock = Mock(side_effect=dao.get_find_by_day_query)
        dao.get_find_by_day_query = get_find_by_day_mock

        execute_and_return_mock = AsyncMock()
        execute_and_return_mock.return_value = mock_entries
        dao.execute_and_return_all = execute_and_return_mock

        # Act
        result = await dao.read_day(test_day, event_type)

        # Assert
        assert result == mock_entries

        args, _ = get_find_by_day_mock.call_args

        assert isinstance(args[0], datetime)
        assert isinstance(args[1], datetime)
        assert isinstance(args[2], ChartEventType)

        assert args[0].hour == 0 and args[0].minute == 0 and args[0].second == 0
        assert args[1].hour == 0 and args[1].minute == 0 and args[1].second == 0

        assert args[0].day + \
            1 == args[1].day, "Expected arg1 to be a day later than arg0"

        args, _ = execute_and_return_mock.call_args

        assert isinstance(args[0], Select)

    @pytest.mark.asyncio
    async def test_read_day_mice(self, dao):

        # Arrange
        clock = SystemClock()  # Could also be userFacingClock for this test
        test_day = test_time
        test_day = test_day - timedelta(days=7)

        mock_entries = [Mock(spec=TimelineEntryObj),
                        Mock(spec=TimelineEntryObj)]

        day_result = ["Precomputed day result"]

        # In order of which they are called:
        with patch.object(dao, 'read_precomputed_entry_for_day') as mocked_precomputed_entry_for_day, \
                patch.object(dao, 'read_day') as mocked_read_day, \
                patch.object(dao, 'create_precomputed_day') as mocked_create_precomputed_day:

            # ### Set up the return values for the mocks
            # Empty list to trigger that path
            mocked_precomputed_entry_for_day.return_value = []  # Nothing
            # Note: For read_day, set up an expected return chain
            mocked_read_day.return_value = mock_entries

            mocked_create_precomputed_day.return_value = day_result

            # Act

            result = await dao.read_day_mice(test_day, clock)

            # Assert
            # The patched methods should have been called
            mocked_precomputed_entry_for_day.assert_called_once()

            mocked_read_day.assert_called_once()
            mocked_read_day.assert_called_once_with(
                test_day, ChartEventType.MOUSE)

            mocked_create_precomputed_day.assert_called_once_with(mock_entries)

            assert isinstance(
                result, list) and len(result) > 0, "create_precomputed_day must return a non-empty list"
            assert result == day_result

    # # FIXME: need more tests for the branches of read_day_peripheral

    @pytest.mark.asyncio
    async def test_read_day_keyboard(self, dao):

        # Arrange
        clock = SystemClock()  # Could also be userFacingClock for this test

        test_day_end = test_time
        test_day_start = test_day_end - timedelta(days=7)

        mock_entries = [Mock(spec=TimelineEntryObj),
                        Mock(spec=TimelineEntryObj)]

        day_result = ["A valid precomputed day of Keyboard Events"]

        # In the order in which they are called
        with patch.object(dao, 'read_precomputed_entry_for_day') as mocked_precomputed_entry_for_day, \
                patch.object(dao, 'read_day') as mocked_read_day, \
                patch.object(dao, 'create_precomputed_day') as mocked_create_precomputed_day:

            # ### Set up return values for the mocks
            # Empty list to trigger the else path (assuming similar logic to read_day_mice)
            mocked_precomputed_entry_for_day.return_value = []
            mocked_read_day.return_value = mock_entries
            mocked_create_precomputed_day.return_value = day_result

            # Act
            result = await dao.read_day_keyboard(test_day_start, clock)

            # ### Assert
            # The patched methods should have been called
            mocked_precomputed_entry_for_day.assert_called_once()

            mocked_read_day.assert_called_once()
            mocked_read_day.assert_called_once_with(
                test_day_start, ChartEventType.KEYBOARD)

            mocked_create_precomputed_day.assert_called_once_with(mock_entries)

            assert isinstance(
                result, list) and len(result) > 0, "create_precomputed_day must return a non-empty list"
            assert result == day_result

    @pytest.mark.asyncio
    async def test_read_all(self, dao, mock_session):
        # Arrange
        mock_entries = [
            Mock(spec=TimelineEntryObj),
            Mock(spec=TimelineEntryObj)
        ]

        execute_and_return_all_mock = AsyncMock()
        execute_and_return_all_mock.return_value = mock_entries
        dao.execute_and_return_all = execute_and_return_all_mock

        # Act
        result = await dao.read_all()

        # Assert
        assert result == mock_entries
        execute_and_return_all_mock.assert_called_once()

        args, _ = execute_and_return_all_mock.call_args

        assert isinstance(args[0], Select)
