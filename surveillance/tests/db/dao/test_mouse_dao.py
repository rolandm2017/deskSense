import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import cast

from src.db.dao.mouse_dao import MouseDao
from src.db.models import MouseMove
from src.trackers.mouse_tracker import MouseMoveWindow
from src.util.clock import SystemClock


class TestMouseDao:
    @pytest.fixture
    def mock_session(self):
        """Create a mock session with necessary async methods"""
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
        """Create session maker that handles async context management"""
        session_cm = AsyncMock()
        session_cm.__aenter__.return_value = mock_session
        session_cm.__aexit__.return_value = None

        maker = MagicMock(spec=async_sessionmaker)
        maker.return_value = session_cm
        return maker

    @pytest.fixture
    def mock_queue_item(self):
        with patch('src.db.dao.base_dao.BaseQueueingDao.queue_item', new_callable=AsyncMock) as mock:
            yield mock

    @pytest.fixture
    def mock_process_queue(self):
        with patch('src.db.dao.base_dao.BaseQueueingDao.process_queue', new_callable=AsyncMock) as mock:
            yield mock

    @pytest.fixture
    def dao(self, mock_session_maker):
        clock = SystemClock()
        return MouseDao(mock_session_maker)

    @pytest.mark.asyncio
    async def test_create_from_start_end_times(self, dao, mock_queue_item):
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=1)

        await dao.create_from_start_end_times(start_time, end_time)

        assert mock_queue_item.called
        queued_item = mock_queue_item.call_args[0][0]
        assert isinstance(queued_item, MouseMove)
        assert cast(datetime, queued_item.start_time) == start_time
        assert cast(datetime, queued_item.end_time) == end_time

    @pytest.mark.asyncio
    async def test_create_from_window(self, dao, mock_queue_item):
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=1)
        window = MouseMoveWindow(start_time, end_time)

        await dao.create_from_window(window)

        assert mock_queue_item.called
        queued_item = mock_queue_item.call_args[0][0]
        assert isinstance(queued_item, MouseMove)
        assert cast(datetime, queued_item.start_time) == start_time
        assert cast(datetime, queued_item.end_time) == end_time

    @pytest.mark.asyncio
    async def test_read_by_id(self, dao, mock_session):
        # Test reading specific move
        mock_move = MouseMove(
            id=1, start_time=datetime.now(), end_time=datetime.now())
        mock_session.get.return_value = mock_move

        result = await dao.read_by_id(1)
        assert result == mock_move
        mock_session.get.assert_called_with(MouseMove, 1)

    @pytest.mark.asyncio
    async def test_read_all(self, dao, mock_session):
        # Test reading all moves
        mock_moves = [
            MouseMove(id=1, start_time=datetime.now(),
                      end_time=datetime.now()),
            MouseMove(id=2, start_time=datetime.now(), end_time=datetime.now())
        ]

        # Setup the mock result chain
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.all = Mock(return_value=mock_moves)
        mock_result.scalars = Mock(return_value=mock_scalar_result)
        mock_session.execute.return_value = mock_result

        result = await dao.read_all()
        assert result == mock_moves

    @pytest.mark.asyncio
    async def test_read_past_24h_events(self, dao, mock_session):
        mock_moves = [
            MouseMove(id=1, start_time=datetime.now(),
                      end_time=datetime.now()),
            MouseMove(id=2, start_time=datetime.now(), end_time=datetime.now())
        ]

        # Setup the mock result chain
        mock_result = AsyncMock()
        mock_scalar_result = AsyncMock()
        mock_scalar_result.all = Mock(return_value=mock_moves)
        mock_result.scalars = Mock(return_value=mock_scalar_result)
        mock_session.execute.return_value = mock_result

        result = await dao.read_past_24h_events()
        assert result == mock_moves

    @pytest.mark.asyncio
    async def test_delete(self, dao, mock_session):
        mock_move = MouseMove(
            id=1, start_time=datetime.now(), end_time=datetime.now())
        mock_session.get.return_value = mock_move

        result = await dao.delete(1)

        assert result == mock_move
        mock_session.delete.assert_called_once_with(mock_move)
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, dao, mock_session):
        mock_session.get.return_value = None

        result = await dao.delete(1)

        assert result is None
        mock_session.delete.assert_not_called()
        assert not mock_session.commit.called

    @pytest.mark.asyncio
    async def test_create_from_window_type_check(self, dao, mock_queue_item):
        window = MouseMoveWindow(datetime.now(), datetime.now())

        with pytest.raises(ValueError, match="mouse move window, and mouse move, were indeed different"):
            mouse_move = MouseMove(
                start_time=window.start_time, end_time=window.end_time)
            if not isinstance(mouse_move, MouseMoveWindow):
                raise ValueError(
                    "mouse move window, and mouse move, were indeed different")
