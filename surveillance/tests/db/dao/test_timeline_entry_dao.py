import pytest
from unittest.mock import AsyncMock, Mock, MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.dao.timeline_entry_dao import TimelineEntryDao
from src.db.models import TimelineEntryObj
from src.object.classes import KeyboardAggregate, MouseMoveWindow
from src.object.enums import ChartEventType
from src.util.clock import SystemClock


class TestTimelineEntryDao:
    @pytest.fixture
    def mock_session(self):
        session = AsyncMock(spec=AsyncSession)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        session.delete = AsyncMock()
        session.get = AsyncMock()
        session.add = AsyncMock()
        return session

    @pytest.fixture
    def mock_session_maker(self, mock_session):
        session_cm = AsyncMock()
        session_cm.__aenter__.return_value = mock_session
        session_cm.__aexit__.return_value = None

        maker = MagicMock(spec=async_sessionmaker)
        maker.return_value = session_cm
        return maker

    @pytest.fixture
    def dao(self, mock_session_maker):
        clock = SystemClock()
        return TimelineEntryDao(clock, mock_session_maker)

    @pytest.mark.asyncio
    async def test_create_from_keyboard_aggregate(self, dao, mock_session):
        # Arrange
        current_time = datetime.now()
        keyboard_aggregate = KeyboardAggregate(
            session_start_time=current_time,
            session_end_time=current_time + timedelta(minutes=5)
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
        assert queued_item.group == ChartEventType.KEYBOARD

    @pytest.mark.asyncio
    async def test_create_from_mouse_move_window(self, dao, mock_session):
        # Arrange
        current_time = datetime.now()
        mouse_window = MouseMoveWindow(
            current_time, current_time + timedelta(minutes=5))

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
        assert queued_item.group == ChartEventType.MOUSE

    @pytest.mark.asyncio
    async def test_read_highest_id(self, dao, mock_session):
        # Arrange
        mock_result = AsyncMock()
        mock_result.scalar = Mock(return_value=5)  # Changed to regular Mock
        mock_session.execute.return_value = mock_result

        # Act
        result = await dao.read_highest_id()

        # Assert
        assert result == 5
        assert mock_session.execute.called

    @pytest.mark.asyncio
    async def test_read_highest_id_empty_table(self, dao, mock_session):
        # Arrange
        mock_result = AsyncMock()
        mock_result.scalar = Mock(return_value=None)  # Changed to regular Mock
        mock_session.execute.return_value = mock_result

        # Act
        result = await dao.read_highest_id()

        # Assert
        assert result == 0
        assert mock_session.execute.called

    @pytest.mark.asyncio
    async def test_read_day(self, dao, mock_session):
        # Arrange
        test_day = datetime.now()
        event_type = ChartEventType.KEYBOARD
        mock_entries = [
            Mock(spec=TimelineEntryObj),
            Mock(spec=TimelineEntryObj)
        ]

        # Setup the mock result chain
        mock_result = AsyncMock()
        mock_scalar_result = Mock()
        mock_scalar_result.all = Mock(return_value=mock_entries)
        mock_result.scalars = Mock(return_value=mock_scalar_result)
        mock_session.execute.return_value = mock_result

        # Act
        result = await dao.read_day(test_day, event_type)

        # Assert
        assert result == mock_entries
        assert mock_session.execute.called

    @pytest.mark.asyncio
    async def test_read_day_mice(self, dao):
        # Arrange
        test_day = datetime.now()
        mock_read_day = AsyncMock()  # Create AsyncMock explicitly
        mock_entries = [Mock(spec=TimelineEntryObj),
                        Mock(spec=TimelineEntryObj)]
        mock_read_day.return_value = mock_entries

        with patch.object(TimelineEntryDao, 'read_day', mock_read_day):
            # Act
            result = await dao.read_day_mice(test_day)

            # Assert
            assert result == mock_entries
            mock_read_day.assert_called_once_with(
                test_day, ChartEventType.MOUSE)

    @pytest.mark.asyncio
    async def test_read_day_keyboard(self, dao):
        # Arrange
        test_day = datetime.now()
        mock_read_day = AsyncMock()  # Create AsyncMock explicitly
        mock_entries = [Mock(spec=TimelineEntryObj),
                        Mock(spec=TimelineEntryObj)]
        mock_read_day.return_value = mock_entries

        with patch.object(TimelineEntryDao, 'read_day', mock_read_day):
            # Act
            result = await dao.read_day_keyboard(test_day)

            # Assert
            assert result == mock_entries
            mock_read_day.assert_called_once_with(
                test_day, ChartEventType.KEYBOARD)

    @pytest.mark.asyncio
    async def test_read_all(self, dao, mock_session):
        # Arrange
        mock_entries = [
            Mock(spec=TimelineEntryObj),
            Mock(spec=TimelineEntryObj)
        ]

        mock_result = AsyncMock()
        mock_scalar_result = Mock()
        mock_scalar_result.all = Mock(return_value=mock_entries)
        mock_result.scalars = Mock(return_value=mock_scalar_result)
        mock_session.execute.return_value = mock_result

        # Act
        result = await dao.read_all()

        # Assert
        assert result == mock_entries
        assert mock_session.execute.called

    @pytest.mark.asyncio
    async def test_delete(self, dao, mock_session):
        # Arrange
        entry_id = 1
        mock_entry = Mock(spec=TimelineEntryObj)
        mock_session.get.return_value = mock_entry

        # Act
        result = await dao.delete(entry_id)

        # Assert
        assert result == mock_entry
        mock_session.delete.assert_called_once_with(mock_entry)
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, dao, mock_session):
        # Arrange
        entry_id = 1
        mock_session.get.return_value = None

        # Act
        result = await dao.delete(entry_id)

        # Assert
        assert result is None
        mock_session.delete.assert_not_called()
        assert not mock_session.commit.called
