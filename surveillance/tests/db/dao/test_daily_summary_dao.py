import pytest
from unittest.mock import AsyncMock, Mock, MagicMock
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.db.dao.daily_summary_dao import DailySummaryDao
from src.db.models import DailyProgramSummary


class TestDailySummaryDao:
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
    def dao(self, mock_session_maker):
        return DailySummaryDao(mock_session_maker)

    @pytest.mark.asyncio
    async def test_create_if_new_else_update_new_entry(self, dao, mock_session):
        # Arrange
        session_data = {
            'window': 'TestProgram',
            'start_time': datetime.now().isoformat(),
            'end_time': (datetime.now().replace(hour=datetime.now().hour + 1)).isoformat()
        }

        # Mock existing entry
        existing_entry = Mock(spec=DailyProgramSummary)
        existing_entry.hours_spent = 1.0
        existing_entry.__str__ = lambda self: f"DailyProgramSummary(hours_spent={
            self.hours_spent})"

        # Mock that no existing entry is found
        mock_result = AsyncMock()
        # Return the actual mock object
        mock_result.scalar_one_or_none.return_value = existing_entry
        mock_session.execute.return_value = mock_result

        # Act
        await dao.create_if_new_else_update(session_data)

        # Assert
        assert mock_session.execute.called

    @pytest.mark.skip(reason="Your skip reason here")
    @pytest.mark.asyncio
    async def test_create_if_new_else_update_existing_entry(self, dao, mock_session):
        # Arrange
        session_data = {
            'window': 'TestProgram',
            'start_time': datetime.now().isoformat(),
            'end_time': (datetime.now().replace(hour=datetime.now().hour + 1)).isoformat()
        }

        # Mock existing entry
        existing_entry = Mock(spec=DailyProgramSummary)
        existing_entry.hours_spent = 1.0

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = existing_entry
        mock_session.execute.return_value = mock_result

        # Act
        await dao.create_if_new_else_update(session_data)

        # Assert
        assert mock_session.execute.called
        assert mock_session.commit.called

    @pytest.mark.asyncio
    async def test_read_day(self, dao, mock_session):
        # Arrange
        test_day = datetime.now()
        mock_entries = [
            Mock(spec=DailyProgramSummary),
            Mock(spec=DailyProgramSummary)
        ]

        # Setup the mock result chain
        mock_result = AsyncMock()
        mock_scalar_result = Mock()
        mock_scalar_result.all = Mock(return_value=mock_entries)
        mock_result.scalars = Mock(return_value=mock_scalar_result)
        mock_session.execute.return_value = mock_result

        # Act
        result = await dao.read_day(test_day)

        # Assert
        assert result == mock_entries
        assert mock_session.execute.called

    @pytest.mark.asyncio
    async def test_read_all(self, dao, mock_session):
        # Arrange
        mock_entries = [
            Mock(spec=DailyProgramSummary),
            Mock(spec=DailyProgramSummary)
        ]

        # Setup the mock result chain
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

    @pytest.mark.skip(reason="Your skip reason here")
    @pytest.mark.asyncio
    async def test_read_row_for_program(self, dao, mock_session):
        # Arrange
        program_name = "TestProgram"
        mock_entry = Mock(spec=DailyProgramSummary)

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_entry
        mock_session.execute.return_value = mock_result

        # Act
        result = await dao.read_row_for_program(program_name)

        # Assert
        assert result == mock_entry
        assert mock_session.execute.called

    @pytest.mark.asyncio
    async def test_delete(self, dao, mock_session):
        # Arrange
        entry_id = 1
        mock_entry = Mock(spec=DailyProgramSummary)
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
