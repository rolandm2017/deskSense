# database.py
import os

from dotenv import load_dotenv

from sqlalchemy import Boolean, Column, DateTime, Integer, String, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from typing import AsyncGenerator, Generator

from activitytracker.config.definitions import program_environment
from activitytracker.util.console_logger import ConsoleLogger

load_dotenv()

ASYNC_DB_URL = os.getenv("ASYNC_DATABASE_URL")

SYNCHRONOUS_DB_URL = os.getenv("SYNCHRONOUS_DB_URL")

SIMULATION_CAPTURE_DB_URL = os.getenv("SIMULATION_CAPTURE_DB_URL")
ASYNC_SIMULATION_CAPTURE_DB_URL = os.getenv("ASYNC_SIMULATION_CAPTURE_DB_URL")

if SYNCHRONOUS_DB_URL is None:
    raise ValueError("Failed to load system power table URL")
if ASYNC_DB_URL is None:
    raise ValueError("Failed to load SqlAlchemy database URL")

if SIMULATION_CAPTURE_DB_URL is None:
    raise ValueError("Simulation db url failed to load")
if ASYNC_SIMULATION_CAPTURE_DB_URL is None:
    raise ValueError("Simulation db url failed to load")


logger = ConsoleLogger()


if program_environment.development:
    logger.log_white("--> Using Development environment")

elif program_environment.data_capture_session:
    logger.log_yellow("Using user input capture session database")

else:
    raise RuntimeError("Unexpected environment")


# Keep references to all engines for potential direct access
development_sync_engine = create_engine(SYNCHRONOUS_DB_URL)
development_async_engine = create_async_engine(ASYNC_DB_URL, echo=False)


regular_session_maker = sessionmaker(
    development_sync_engine, class_=Session, expire_on_commit=False
)

async_session_maker = async_sessionmaker(
    development_async_engine, class_=AsyncSession, expire_on_commit=False
)

simulation_sync_engine = create_engine(SIMULATION_CAPTURE_DB_URL)
simulation_async_engine = create_async_engine(ASYNC_SIMULATION_CAPTURE_DB_URL, echo=False)

simulation_regular_session_maker = sessionmaker(
    simulation_sync_engine, class_=Session, expire_on_commit=False
)
simulation_async_session_maker = async_sessionmaker(
    simulation_async_engine, class_=AsyncSession, expire_on_commit=False
)


Base = declarative_base()

# Dependency for FastAPI endpoints


# Modified get_db to include schema setting
def get_db() -> Generator[Session, None, None]:
    if program_environment.development:
        with regular_session_maker() as session:
            try:
                yield session
            finally:
                session.close()
    else:
        # Use get_simulation_db directly if in data capture session
        yield from get_simulation_db()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    if program_environment.development:
        async with async_session_maker() as session:
            try:
                yield session
            finally:
                await session.close()
    else:
        # Use get_async_simulation_db directly
        async for session in get_async_simulation_db():
            yield session


# async def init_db() -> None:
#     """Initialize the database by creating all tables if they don't exist."""
#     pass
#     # async with async_engine.begin() as conn:
#     # No longer doing automatic create_all
#     # as it takes the db out of sync with Alembic
#     # await conn.run_sync(Base.metadata.create_all)
