import pytest
from unittest.mock import AsyncMock, patch, Mock, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.object.dto import TypingSessionDto
from src.db.dao.keyboard_dao import KeyboardDao
from src.db.models import TypingSession
from src.object.classes import KeyboardAggregate
from src.util.clock import SystemClock


class TestKeyboardDao:
    @pytest.fixture
    def mock_session(self):
        """Create a mock session with all necessary async methods"""
        session = AsyncMock(spec=AsyncSession)
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        session.delete = AsyncMock()
        session.get = AsyncMock()
        return session

    @pytest.fixture
    def mock_session_maker(self, mock_session):
        """Create a session maker that properly handles async context management"""
        async def async_session_cm():
            yield mock_session

        # Create an async context manager mock
        session_cm = AsyncMock()
        session_cm.__aenter__.return_value = mock_session
        session_cm.__aexit__.return_value = None

        # Create the session maker mock
        maker = MagicMock(spec=async_sessionmaker)
        maker.return_value = session_cm
        return maker

    @pytest.fixture
    def dao(self, mock_session_maker):
        clock = SystemClock()
        return KeyboardDao(clock, mock_session_maker)

    @pytest.mark.asyncio
    async def test_create(self, dao, mock_session_maker):
        # Arrange
        session = KeyboardAggregate(
            start_time=datetime.now(),
            end_time=datetime.now()
        )

        # Act
        await dao.create(session)

        # Assert
        assert dao.queue.qsize() > 0

    @pytest.mark.asyncio
    async def test_read_all(self, dao, mock_session):
        # Arrange
        mock_typing_sessions = [
            Mock(spec=TypingSession, id=1,
                 start_time=datetime.now(), end_time=datetime.now()),
            Mock(spec=TypingSession, id=2,
                 start_time=datetime.now(), end_time=datetime.now())
        ]
        result_mock = Mock()
        result_mock.all.return_value = [(session,)
                                        for session in mock_typing_sessions]
        mock_session.execute.return_value = result_mock

        # Act
        result = await dao.read_all()

        # Assert
        assert len(result) == 2
        assert all(isinstance(r, TypingSessionDto) for r in result)
        assert [r.id for r in result] == [1, 2]

    @pytest.mark.asyncio
    async def test_read_past_24h_events(self, dao, mock_session):
        # Arrange
        current_time = datetime.now()

        # Create proper mock session objects
        mock_typing_sessions = [
            TypingSession(
                id=1,
                start_time=current_time,
                end_time=current_time
            ),
            TypingSession(
                id=2,
                start_time=current_time - timedelta(hours=1),
                end_time=current_time
            )
        ]

        # Create result mock
        mock_result = AsyncMock()
        mock_result.all = Mock(
            return_value=[(session,) for session in mock_typing_sessions])
        mock_session.execute = AsyncMock(return_value=mock_result)

        # Act
        result = await dao.read_past_24h_events()

        # Assert
        assert len(result) == 2
        assert all(isinstance(r, TypingSessionDto) for r in result)
        assert result[0].id == 1
        assert result[1].id == 2

    @pytest.mark.asyncio
    async def test_read_past_24h_events_db_failure(self, dao, mock_session):
        # Arrange
        mock_session.execute.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Failed to read typing sessions"):
            await dao.read_past_24h_events()

    @pytest.mark.asyncio
    async def test_delete(self, dao, mock_session):
        # Arrange
        mock_typing_session = Mock(spec=TypingSession, id=1)
        mock_session.get.return_value = mock_typing_session

        # Act
        result = await dao.delete(1)

        # Assert
        assert result == mock_typing_session
        mock_session.delete.assert_called_once_with(mock_typing_session)
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, dao, mock_session):
        # Arrange
        mock_session.get.return_value = None

        # Act
        result = await dao.delete(1)

        # Assert
        assert result is None
        mock_session.delete.assert_not_called()
        assert not mock_session.commit.called
