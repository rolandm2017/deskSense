# database.py
import os

from dotenv import load_dotenv

from sqlalchemy import Boolean, Column, DateTime, Integer, String, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from typing import AsyncGenerator

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


class Environment:
    def __init__(self) -> None:
        self.development = False
        self.data_capture_session = True
        self.simulated_usage = False


environment = Environment()

if environment.development:
    logger.log_white("Using Development environment")
    engine = create_engine(SYNCHRONOUS_DB_URL)

    async_engine = create_async_engine(
        ASYNC_DB_URL,
        echo=False,  # Set to True for SQL query logging
    )

elif environment.data_capture_session:
    logger.log_yellow("Using user input capture session database")
    engine = create_engine(SIMULATION_CAPTURE_DB_URL)
    async_engine = create_async_engine(ASYNC_SIMULATION_CAPTURE_DB_URL, echo=False)
else:
    raise RuntimeError("Unexpected environment")


regular_session_maker = sessionmaker(engine, class_=Session, expire_on_commit=False)

async_session_maker = async_sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


# Keep references to all engines for potential direct access
development_sync_engine = create_engine(SYNCHRONOUS_DB_URL)
development_async_engine = create_async_engine(ASYNC_DB_URL, echo=False)
simulation_sync_engine = create_engine(SIMULATION_CAPTURE_DB_URL)
simulation_async_engine = create_async_engine(ASYNC_SIMULATION_CAPTURE_DB_URL, echo=False)


Base = declarative_base()

# Dependency for FastAPI endpoints


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize the database by creating all tables if they don't exist."""
    async with engine.begin() as conn:
        pass
        # No longer doing automatic create_all
        # as it takes the db out of sync with Alembic
        # await conn.run_sync(Base.metadata.create_all)
