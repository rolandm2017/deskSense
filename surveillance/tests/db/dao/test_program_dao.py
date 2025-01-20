import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.dao.program_dao import ProgramDao
from src.db.models import Program
from src.object.classes import SessionData


@pytest_asyncio.fixture
async def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest_asyncio.fixture
def program_dao(mock_db):
    return ProgramDao(db=mock_db)


@pytest.mark.asyncio
async def test_create_happy_path(program_dao):
    # Arrange
    session = {
        'window': 'TestWindow',
        'start_time': datetime.now().isoformat(),
        'end_time': (datetime.now() + timedelta(hours=1)).isoformat(),
        'productive': True
    }

    program_dao.queue_item = AsyncMock()

    # Act
    await program_dao.create(session)

    # Assert
    program_dao.queue_item.assert_called_once_with(session)


@pytest.mark.asyncio
async def test_create_without_queue_happy_path(program_dao):
    session = {
        'window': 'TestWindow',
        'start_time': datetime.now().isoformat(),
        'end_time': (datetime.now() + timedelta(hours=1)).isoformat(),
        'productive': True
    }

    mock_program = Mock(spec=Program)
    program_dao.db.add = AsyncMock()
    program_dao.db.commit = AsyncMock()
    program_dao.db.refresh = AsyncMock()

    # Add awaits here
    result = await program_dao.create_without_queue(session)
    await program_dao.db.add(mock_program)
    await program_dao.db.commit()
    await program_dao.db.refresh(mock_program)

    assert result is not None


@pytest.mark.asyncio
async def test_create_without_queue_sad_path(program_dao):
    # Arrange
    session = "invalid_session"

    # Act
    result = await program_dao.create_without_queue(session)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_read_happy_path(program_dao):
    # Arrange
    mock_programs = [Mock(spec=Program), Mock(spec=Program)]
    program_dao.db.execute = AsyncMock(return_value=Mock(
        scalars=Mock(return_value=mock_programs)))

    # Mock result.scalars().all()
    mock_execute_result = Mock()
    mock_execute_result.scalars = Mock()
    mock_execute_result.scalars.return_value = Mock()
    mock_execute_result.scalars.return_value.all = Mock(
        return_value=mock_programs)

    # Make db.execute return the awaitable that resolves to our mock
    program_dao.db.execute = AsyncMock(return_value=mock_execute_result)

    # Act
    result = await program_dao.read()

    # Assert
    program_dao.db.execute.assert_called_once()
    assert len(result) == len(mock_programs)


@pytest.mark.asyncio
async def test_read_with_id_happy_path(program_dao):
    # Arrange
    program_id = 1
    mock_program = Mock(spec=Program)
    program_dao.db.get = AsyncMock(return_value=mock_program)

    # Act
    result = await program_dao.read(program_id=program_id)

    # Assert
    program_dao.db.get.assert_called_once_with(Program, program_id)
    assert result == mock_program


@pytest.mark.asyncio
async def test_read_past_24h_events_happy_path(program_dao):
    # Arrange
    mock_programs = [Mock
                     (spec=Program), Mock(spec=Program)]

    # Mock result.scalars().all()
    mock_execute_result = Mock()
    mock_execute_result.scalars = Mock()
    mock_execute_result.scalars.return_value = Mock()
    mock_execute_result.scalars.return_value.all = Mock(
        return_value=mock_programs)

    # Make db.execute return the awaitable that resolves to our mock
    program_dao.db.execute = AsyncMock(return_value=mock_execute_result)

    # program_dao.db.execute = AsyncMock(return_value=Mock(
    # scalars=Mock(return_value=mock_programs)))

    # Act
    result = await program_dao.read_past_24h_events()

    # Assert
    program_dao.db.execute.assert_called_once()
    assert len(result) == len(mock_programs)


@pytest.mark.asyncio
async def test_delete_happy_path(program_dao):
    # Arrange
    program_id = 1
    mock_program = Mock(spec=Program)
    program_dao.db.get = AsyncMock(return_value=mock_program)
    program_dao.db.delete = AsyncMock()
    program_dao.db.commit = AsyncMock()

    # Act
    result = await program_dao.delete(program_id)

    # Assert
    program_dao.db.get.assert_called_once_with(Program, program_id)
    program_dao.db.delete.assert_called_once_with(mock_program)
    program_dao.db.commit.assert_called_once()
    assert result == mock_program


@pytest.mark.asyncio
async def test_delete_sad_path(program_dao):
    # Arrange
    program_id = 1
    program_dao.db.get = AsyncMock(return_value=None)

    # Act
    result = await program_dao.delete(program_id)

    # Assert
    program_dao.db.get.assert_called_once_with(Program, program_id)
    assert result is None
