# activitytracker/db/db_session.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from typing import AsyncGenerator, Generator

from activitytracker.config.definitions import program_environment
from activitytracker.db.database import async_session_maker, regular_session_maker

# Forward declaration - these will be imported at function level to avoid circular imports
get_simulation_db = None
get_async_simulation_db = None


def get_db() -> Generator[Session, None, None]:
    """Get database session based on current environment."""
    if program_environment.development:
        with regular_session_maker() as session:
            try:
                yield session
            finally:
                session.close()
    else:
        # Import at function level to avoid circular imports
        from activitytracker.input_capture.test_schema_manager import (
            get_simulation_db as _get_simulation_db,
        )

        global get_simulation_db
        get_simulation_db = _get_simulation_db

        # Use get_simulation_db
        yield from get_simulation_db()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session based on current environment."""
    if program_environment.development:
        async with async_session_maker() as session:
            try:
                yield session
            finally:
                await session.close()
    else:
        # Import at function level to avoid circular imports
        from activitytracker.input_capture.test_schema_manager import (
            get_async_simulation_db as _get_async_simulation_db,
        )

        global get_async_simulation_db
        get_async_simulation_db = _get_async_simulation_db

        # Use get_async_simulation_db
        async for session in get_async_simulation_db():
            yield session
