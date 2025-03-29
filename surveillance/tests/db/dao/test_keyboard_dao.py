import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, patch, Mock, MagicMock
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import text

from src.object.dto import TypingSessionDto
from src.db.dao.keyboard_dao import KeyboardDao
from src.db.models import TypingSession
from src.object.classes import KeyboardAggregate
from src.util.clock import SystemClock


async def truncate_table(async_session_maker):
    """Utility function to truncate a specific table for testing purposes.
    Should ONLY be used in test environments."""
    async with async_session_maker() as session:
        async with session.begin():
            # Using raw SQL to truncate the table and reset sequences
            await session.execute(text(f'TRUNCATE TABLE typing_sessions RESTART IDENTITY CASCADE'))

@pytest_asyncio.fixture
async def dao( async_engine_and_asm):
    _, asm = async_engine_and_asm
    yield KeyboardDao(asm)
    await truncate_table(asm)

@pytest.mark.asyncio
async def test_create( dao):
    # Arrange
    session = KeyboardAggregate(
        start_time=datetime.now(),
        end_time=datetime.now()
    )

    # Act
    await dao.create(session)

    # Assert
    assert dao.queue.qsize() > 0

    await asyncio.sleep(0.05)

    # And you can take it back out:
    v = await dao.read_all()
    assert len(v) == 1


@pytest.mark.asyncio
async def test_read_all( dao):

    # Write two dummy results
    s = KeyboardAggregate(
        start_time=datetime.now(),
        end_time=datetime.now()
    )
    s2 = KeyboardAggregate(
        start_time=datetime.now(),
        end_time=datetime.now()
    )
    await dao.create(s)
    await dao.create(s2)
    await asyncio.sleep(0.05)

    # Act
    result = await dao.read_all()

    # Assert
    assert len(result) == 2
    assert all(isinstance(r, TypingSessionDto) for r in result)
    assert [r.id for r in result] == [1, 2]

@pytest.mark.asyncio
async def test_read_past_24h_events( dao):
    # Arrange
    current_time = datetime.now()

    s = KeyboardAggregate(
        start_time=datetime.now(),
        end_time=datetime.now()
    )
    s2 = KeyboardAggregate(
        start_time=datetime.now(),
        end_time=datetime.now()
    )
    await dao.create(s)
    await dao.create(s2)
    await asyncio.sleep(0.05)


    # Act
    result = await dao.read_past_24h_events(current_time)

    # Assert
    assert len(result) == 2
    assert all(isinstance(r, TypingSessionDto) for r in result)
    assert result[0].id == 1
    assert result[1].id == 2

@pytest.mark.asyncio
async def test_delete( dao):
    pass  # TODO

@pytest.mark.asyncio
async def test_delete_nonexistent( dao):
    # TODO:
    pass