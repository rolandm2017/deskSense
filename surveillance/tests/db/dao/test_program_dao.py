import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import text


from src.db.dao.program_dao import ProgramDao
from src.db.models import Program
from src.object.classes import ProgramSessionData
from src.util.clock import SystemClock

async def truncate_table(async_session_maker):
    """Utility function to truncate a specific table for testing purposes.
    Should ONLY be used in test environments."""
    async with async_session_maker() as session:
        async with session.begin():
            # Using raw SQL to truncate the table and reset sequences
            await session.execute(text(f'TRUNCATE TABLE program_changes RESTART IDENTITY CASCADE'))

class TestProgramDao:
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
    
    @pytest_asyncio.fixture()
    async def dao(self, async_engine_and_asm):
        """Create a fresh DAO for each test"""
        _, asm = async_engine_and_asm
        dao_instance = ProgramDao(asm)
        yield dao_instance
        # Explicit cleanup if needed
        await dao_instance.cleanup()
        await truncate_table(asm)

    @pytest.mark.asyncio
    async def test_create_happy_path(self, dao):
        # Arrange
        session = ProgramSessionData()
        session.window_title = "MyTestWindow"
        session.detail = "Test detail for the test"
        session.start_time = datetime.now()
        session.end_time = datetime.now() + timedelta(minutes=3)
        session.productive = True

        original_queue_item = dao.queue_item
        queue_item_spy = AsyncMock(side_effect=original_queue_item)
        dao.queue_item = queue_item_spy


        # Act
        await dao.create(session)

        # Assert
        expected_call_argument = Program(
            window=session.window_title,
            detail=session.detail,
            start_time=session.start_time,
            end_time=session.end_time,
            productive=session.productive
        )
        queue_item_spy.assert_called_once_with(expected_call_argument)

    # FIXME:
    # FIXME: OSError when running "pytest" (if you don't see it, check that pytest doesn't use --capture=no silently in settings)
    # FIXME:
    # FIXME:

    # @pytest.mark.asyncio
    # async def test_read_by_id(self, dao, mock_session):
    #     # Test reading specific program
    #     program_id = 1
    #     mock_program = Mock(spec=Program)
    #     mock_session.get.return_value = mock_program

    #     result = await dao.read_by_id(program_id)
    #     assert result == mock_program
    #     mock_session.get.assert_called_with(Program, program_id)

    # @pytest.mark.asyncio
    # async def test_read_all(self, dao, mock_session):
    #     # Test reading all programs
    #     mock_programs = [
    #         Mock(spec=Program, id=1),
    #         Mock(spec=Program, id=2)
    #     ]

    #     # Setup the mock result chain
    #     mock_result = AsyncMock()
    #     mock_scalar_result = Mock()  # Changed to regular Mock
    #     mock_scalar_result.all = Mock(
    #         return_value=mock_programs)  # Changed to regular Mock
    #     mock_result.scalars = Mock(return_value=mock_scalar_result)
    #     mock_session.execute.return_value = mock_result

    #     result = await dao.read_all()
    #     assert result == mock_programs

    # @pytest.mark.asyncio
    # async def test_read_past_24h_events(self, dao, mock_session):
    #     mock_programs = [
    #         Mock(spec=Program, id=1),
    #         Mock(spec=Program, id=2)
    #     ]

    #     # Setup the mock result chain
    #     mock_result = AsyncMock()
    #     mock_scalar_result = Mock()  # Changed to regular Mock
    #     mock_scalar_result.all = Mock(
    #         return_value=mock_programs)  # Changed to regular Mock
    #     mock_result.scalars = Mock(return_value=mock_scalar_result)
    #     mock_session.execute.return_value = mock_result

    #     result = await dao.read_past_24h_events(datetime.now())
    #     assert result == mock_programs
    #     assert mock_session.execute.called

    # @pytest.mark.asyncio
    # async def test_delete(self, dao, mock_session):
    #     # Arrange
    #     program_id = 1
    #     mock_program = Mock(spec=Program)
    #     mock_session.get.return_value = mock_program

    #     # Act
    #     result = await dao.delete(program_id)

    #     # Assert
    #     assert result == mock_program
    #     mock_session.delete.assert_called_once_with(mock_program)
    #     assert mock_session.commit.called

    # @pytest.mark.asyncio
    # async def test_delete_nonexistent(self, dao, mock_session):
    #     # Arrange
    #     program_id = 1
    #     mock_session.get.return_value = None

    #     # Act
    #     result = await dao.delete(program_id)

    #     # Assert
    #     assert result is None
    #     mock_session.delete.assert_not_called()
    #     assert not mock_session.commit.called
