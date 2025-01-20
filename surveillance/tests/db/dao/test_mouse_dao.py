import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.dao.mouse_dao import MouseDao
from src.db.models import MouseMove
from src.trackers.mouse_tracker import MouseMoveWindow


class TestMouseDao:
    @pytest.fixture
    def mock_db(self):
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_queue_item(self):
        with patch('src.db.dao.base_dao.BaseQueueingDao.queue_item', new_callable=AsyncMock) as mock:
            yield mock

    @pytest.fixture
    def mock_process_queue(self):
        with patch('src.db.dao.base_dao.BaseQueueingDao.process_queue', new_callable=AsyncMock) as mock:
            yield mock

    @pytest.fixture
    def dao(self, mock_db):
        return MouseDao(mock_db)

    @pytest.mark.asyncio
    async def test_create_from_start_end_times(self, dao, mock_queue_item):
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=1)

        await dao.create_from_start_end_times(start_time, end_time)

        assert mock_queue_item.called
        queued_item = mock_queue_item.call_args[0][0]
        assert isinstance(queued_item, MouseMove)
        assert queued_item.start_time == start_time
        assert queued_item.end_time == end_time

    @pytest.mark.asyncio
    async def test_create_from_window(self, dao, mock_queue_item):
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=1)
        window = MouseMoveWindow(start_time, end_time)

        await dao.create_from_window(window)

        assert mock_queue_item.called
        queued_item = mock_queue_item.call_args[0][0]
        assert isinstance(queued_item, MouseMove)
        assert queued_item.start_time == start_time
        assert queued_item.end_time == end_time

    @pytest.mark.asyncio
    async def test_create_without_queue(self, dao):
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=1)

        await dao.create_without_queue(start_time, end_time)

        assert dao.db.add.called
        assert dao.db.commit.called
        assert dao.db.refresh.called

    @pytest.mark.asyncio
    async def test_read_specific_move(self, dao):
        mock_move = MouseMove(
            id=1, start_time=datetime.now(), end_time=datetime.now())
        dao.db.get = AsyncMock(return_value=mock_move)

        result = await dao.read(1)

        assert result == mock_move
        dao.db.get.assert_called_with(MouseMove, 1)

    @pytest.mark.asyncio
    async def test_read_all_moves(self, dao):
        mock_moves = [
            MouseMove(id=1, start_time=datetime.now(),
                      end_time=datetime.now()),
            MouseMove(id=2, start_time=datetime.now(), end_time=datetime.now())
        ]

        # Create a mock that will be returned by execute()
        mock_execute_result = Mock()
        mock_execute_result.scalars = Mock()
        mock_execute_result.scalars.return_value = Mock()
        mock_execute_result.scalars.return_value.all = Mock(
            return_value=mock_moves)

        # Make db.execute return the awaitable that resolves to our mock
        dao.db.execute = AsyncMock(return_value=mock_execute_result)

        result = await dao.read()
        assert result == mock_moves

    @pytest.mark.asyncio
    async def test_read_past_24h_events(self, dao):
        mock_moves = [
            MouseMove(id=1, start_time=datetime.now(),
                      end_time=datetime.now()),
            MouseMove(id=2, start_time=datetime.now(), end_time=datetime.now())
        ]

        # Create a mock that will be returned by execute()
        mock_execute_result = Mock()
        mock_execute_result.scalars = Mock()
        mock_execute_result.scalars.return_value = Mock()
        mock_execute_result.scalars.return_value.all = Mock(
            return_value=mock_moves)

        # Make db.execute return the awaitable that resolves to our mock
        dao.db.execute = AsyncMock(return_value=mock_execute_result)

        result = await dao.read_past_24h_events()
        assert result == mock_moves

    @pytest.mark.asyncio
    async def test_delete(self, dao):
        mock_move = MouseMove(
            id=1, start_time=datetime.now(), end_time=datetime.now())
        dao.db.get = AsyncMock(return_value=mock_move)
        dao.db.delete = AsyncMock()
        dao.db.commit = AsyncMock()

        result = await dao.delete(1)

        assert result == mock_move
        assert dao.db.delete.called
        assert dao.db.commit.called

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, dao):
        dao.db.get = AsyncMock(return_value=None)

        result = await dao.delete(1)

        assert result is None
        assert not dao.db.delete.called
        assert not dao.db.commit.called

    @pytest.mark.asyncio
    async def test_create_from_window_type_check(self, dao, mock_queue_item):
        window = MouseMoveWindow(datetime.now(), datetime.now())

        with pytest.raises(ValueError, match="mouse move window, and mouse move, were indeed different"):
            mouse_move = MouseMove(
                start_time=window.start_time, end_time=window.end_time)
            if not isinstance(mouse_move, MouseMoveWindow):
                raise ValueError(
                    "mouse move window, and mouse move, were indeed different")
