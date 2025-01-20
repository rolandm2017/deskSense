import pytest
from unittest.mock import AsyncMock, patch, Mock
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession


from src.object.dto import TypingSessionDto
from src.db.dao.keyboard_dao import KeyboardDao
from src.db.models import TypingSession
from src.object.classes import KeyboardAggregate
from src.object.dto import TypingSessionDto


class MockTypingSession:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @classmethod
    def __instancecheck__(cls, instance):
        return isinstance(instance, Mock) and all(hasattr(instance, attr) for attr in ['id', 'start_time', 'end_time'])


class TestKeyboardDao:
    @pytest.fixture
    def mock_db(self):
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_queue_item(self):
        with patch('src.db.dao.base_dao.BaseQueueingDao.queue_item', new_callable=AsyncMock) as mock:
            yield mock

    @pytest.fixture
    def dao(self, mock_db):
        return KeyboardDao(mock_db)

    @pytest.mark.asyncio
    async def test_create(self, dao, mock_queue_item):
        session = KeyboardAggregate(
            session_start_time=datetime.now(), session_end_time=datetime.now())

        await dao.create(session)

        assert mock_queue_item.called
        queued_item = mock_queue_item.call_args[0][0]
        assert isinstance(queued_item, KeyboardAggregate)
        assert queued_item.session_start_time == session.session_start_time
        assert queued_item.session_end_time == session.session_end_time

    @pytest.mark.asyncio
    async def test_create_without_queue(self, dao):
        session = KeyboardAggregate(
            session_start_time=datetime.now(), session_end_time=datetime.now())

        result = await dao.create_without_queue(session)

        assert dao.db.add.called
        assert dao.db.commit.called
        assert dao.db.refresh.called
        assert result.start_time == session.session_start_time
        assert result.end_time == session.session_end_time

    @pytest.mark.asyncio
    async def test_read_specific_keystroke(self, dao):
        mock_keystroke = TypingSession(
            id=1, start_time=datetime.now(), end_time=datetime.now())
        dao.db.get = AsyncMock(return_value=mock_keystroke)

        result = await dao.read_by_id(1)

        assert result == mock_keystroke
        dao.db.get.assert_called_with(TypingSession, 1)

    @pytest.mark.asyncio
    async def test_read_all_keystrokes(self, dao):
        mock_keystrokes = [
            [TypingSession(id=1, start_time=datetime.now(),
                           end_time=datetime.now())],
            [TypingSession(id=2, start_time=datetime.now(),
                           end_time=datetime.now())],
        ]

        mock_execute_result = Mock()
        mock_execute_result.all = Mock(
            return_value=mock_keystrokes)

        dao.db.execute = AsyncMock(return_value=mock_execute_result)

        result = await dao.read_all()
        assert result[0].id == mock_keystrokes[0][0].id
        assert result[1].id == mock_keystrokes[1][0].id
        assert result[0].start_time == mock_keystrokes[0][0].start_time
        assert result[1].start_time == mock_keystrokes[1][0].start_time

    @pytest.mark.asyncio
    async def test_read_past_24h_events(self, dao):
        mock_typing_sessions = [[
            Mock(id=1, start_time=datetime.now(),
                 end_time=datetime.now() + timedelta(minutes=10)),
            Mock(id=2, start_time=datetime.now() -
                 timedelta(hours=1), end_time=datetime.now())
        ]]

        mock_execute_result = Mock()  # Mock object to mimic the result of db.execute()
        mock_execute_result.all = Mock(
            return_value=mock_typing_sessions)  # Configure .all()

        # Mock self.db.execute to return the mock result
        dao.db.execute = AsyncMock(return_value=mock_execute_result)

        # Call the method under test
        result = await dao.read_past_24h_events()

        # Assertions
        assert len(result) == len(mock_typing_sessions)
        assert all(isinstance(r, TypingSessionDto) for r in result)

    @pytest.mark.asyncio
    async def test_delete_existing_keystroke(self, dao):
        mock_keystroke = TypingSession(
            id=1, start_time=datetime.now(), end_time=datetime.now())
        dao.db.get = AsyncMock(return_value=mock_keystroke)
        dao.db.delete = AsyncMock()
        dao.db.commit = AsyncMock()

        result = await dao.delete(1)

        assert result == mock_keystroke
        dao.db.delete.assert_called_with(mock_keystroke)
        assert dao.db.commit.called

    @pytest.mark.asyncio
    async def test_delete_nonexistent_keystroke(self, dao):
        dao.db.get = AsyncMock(return_value=None)

        result = await dao.delete(1)

        assert result is None
        assert not dao.db.delete.called
        assert not dao.db.commit.called

    # FIXME - failing + warning tests start here

    @pytest.mark.asyncio
    async def test_read_past_24h_events_happy_path(self, dao):
        # Arrange
        # dao = KeyboardDao()

        # Create mock TypingSession objects
        mock_typing_sessions = [
            Mock(id=1, start_time=datetime.now(),
                 end_time=datetime.now() + timedelta(minutes=10)),
            Mock(id=2, start_time=datetime.now() -
                 timedelta(hours=1), end_time=datetime.now())
        ]

        # Simulate `result.all()` returning the list of mock objects
        mock_execute_result = Mock()
        mock_execute_result.all = Mock(return_value=mock_typing_sessions)

        # Mock DAO database execution
        dao.db.execute = AsyncMock(return_value=mock_execute_result)

        # Act
        with pytest.raises(RuntimeError, match="Failed to read typing sessions"):
            result = await dao.read_past_24h_events()

            # Assert
            assert len(result) == len(mock_typing_sessions)
            assert all(isinstance(r, TypingSessionDto) for r in result)
            assert [r.id for r in result] == [
                ts.id for ts in mock_typing_sessions]

    @pytest.mark.asyncio
    async def test_read_past_24h_events_empty_result(self, dao):
        # Arrange
        # dao = KeyboardDao()
        mock_execute_result = Mock()
        mock_execute_result.all = Mock(return_value=[])
        dao.db.execute = AsyncMock(return_value=mock_execute_result)

        # Act
        result = await dao.read_past_24h_events()

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_read_past_24h_events_invalid_data(self, dao):
        # Arrange
        # dao = KeyboardDao()
        mock_typing_sessions = [
            (None,),  # Invalid row
            Mock(id=2, start_time=datetime.now() - \
                 timedelta(hours=1), end_time=datetime.now())
        ]
        mock_execute_result = Mock()
        mock_execute_result.all = Mock(return_value=mock_typing_sessions)
        dao.db.execute = AsyncMock(return_value=mock_execute_result)

        # Act
        with pytest.raises(RuntimeError, match="Failed to read typing sessions"):
            result = await dao.read_past_24h_events()

        # Assert
            assert len(result) == 1
            assert isinstance(result[0], TypingSessionDto)

    @pytest.mark.asyncio
    async def test_read_past_24h_events_db_failure(self, dao):
        # Arrange
        # dao = KeyboardDao()
        dao.db.execute = AsyncMock(side_effect=Exception("Database error"))

        # Act & Assert
        with pytest.raises(RuntimeError, match="Failed to read typing sessions"):
            await dao.read_past_24h_events()
