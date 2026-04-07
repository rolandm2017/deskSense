# conftest.py
import os
import sys
from pathlib import Path

import pytest_asyncio
from dotenv import load_dotenv

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from activitytracker.db.models import Base
from tests.helper.truncation import truncate_all_tables_via_engine

# Force Windows to use the SelectEventLoop instead of ProactorEventLoop
# This needs to happen before any asyncio code runs
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


####

pytest_plugins = ["pytest_asyncio"]


# Fixture allegedly solves
# >       response = await async_client.get("http://127.0.0.1:8000/dashboard/timeline")
# E       AttributeError: 'async_generator' object has no attribute 'get'


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


def pytest_configure(config):
    config.option.asyncio_default_fixture_loop_scope = "function"


#
# # Make the tests run fine on both Ubuntu AND Windows
#


# Get the absolute path to the project root
def setup_paths_for_windows():
    """Was found running outside of a func when brought over from Windows"""
    project_root = Path(__file__).absolute().parent

    # Add both the project root and the src directory to the path
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "src"))

    # Print paths for debugging
    print(f"Project root added to path: {project_root}")
    print(f"Sys path: {sys.path}")


#
#
# #### #### #### ####
#
# Mock fixtures section
#
# #### #### #### ####
#
#


@pytest.fixture
def mock_session():
    session = Mock(spec=Session)
    session.commit = Mock()
    session.refresh = Mock()
    session.execute = Mock()
    session.delete = Mock()
    session.get = Mock()
    session.add = Mock()
    return session


@pytest.fixture
def mock_async_session():
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.delete = AsyncMock()
    session.get = AsyncMock()
    session.add = AsyncMock()
    return session


@pytest.fixture
def mock_regular_session_maker(mock_session):
    print("WARNING: Mock session makers don't do anything")
    session_cm = AsyncMock()
    session_cm.__aenter__.return_value = mock_session
    session_cm.__aexit__.return_value = None

    maker = MagicMock(spec=sessionmaker)
    maker.return_value = session_cm
    return maker


@pytest.fixture
def mock_async_session_maker(mock_async_session):
    session_cm = AsyncMock()
    session_cm.__aenter__.return_value = mock_async_session
    session_cm.__aexit__.return_value = None

    maker = MagicMock(spec=async_sessionmaker)
    maker.return_value = session_cm
    return maker


#
#
# #### #### #### ####
#
# Integration test fixtures section
#
# #### #### #### ####
#
#


load_dotenv()

ASYNC_TEST_DB_URL = ASYNC_TEST_DB_URL = os.getenv("ASYNC_TEST_DB_URL")


@pytest.fixture(scope="session")
def postgres_test_db():
    """Create the PostgreSQL test database once for the whole test session."""
    if SYNC_TEST_DB_URL is None:
        raise ValueError("SYNC_TEST_DB_URL environment variable is not set")

    sync_test_db_url = make_url(SYNC_TEST_DB_URL)
    test_db_name = sync_test_db_url.database
    default_url = sync_test_db_url.set(database="postgres")
    admin_engine = create_engine(default_url, isolation_level="AUTOCOMMIT")

    with admin_engine.connect() as conn:
        conn.execute(
            text(
                """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = :db_name
            AND pid <> pg_backend_pid()
        """
            ),
            {"db_name": test_db_name},
        )
        conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
        conn.execute(text(f"CREATE DATABASE {test_db_name}"))

    admin_engine.dispose()

    try:
        yield
    finally:
        admin_engine = create_engine(default_url, isolation_level="AUTOCOMMIT")
        with admin_engine.connect() as conn:
            conn.execute(
                text(
                    """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = :db_name
                AND pid <> pg_backend_pid()
            """
                ),
                {"db_name": test_db_name},
            )
            conn.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
        admin_engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def global_test_engine(postgres_test_db):
    """Create a single async engine shared across the whole test session."""

    test_engine = create_async_engine(
        ASYNC_TEST_DB_URL,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_timeout=30,
        max_overflow=10,
        pool_size=5,
    )

    try:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield test_engine
    finally:
        await test_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_engine_and_asm(global_test_engine, postgres_db_isolation):
    """Provide the shared async engine plus a fresh session maker for this test."""
    async_session_maker = async_sessionmaker(
        global_test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=True,
        autocommit=False,
    )

    yield global_test_engine, async_session_maker


@pytest_asyncio.fixture(scope="function")
async def plain_asm(async_engine_and_asm):
    """Extract just the session maker from the engine fixture"""
    _, asm = async_engine_and_asm
    return asm


@pytest_asyncio.fixture(scope="function")
async def async_engine(async_engine_and_asm):
    """Extract just the engine from the fixture"""
    engine, _ = async_engine_and_asm
    return engine


@pytest_asyncio.fixture
async def async_db_session_in_mem():
    # Create an async in-memory SQLite database
    # Note: SQLite needs special URI format for async mode
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # Create all tables defined in your models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create async session
    session_maker: async_sessionmaker = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    yield engine, session_maker

    async with session_maker() as session:
        await session.rollback()

    # Teardown: drop all tables
    async with engine.begin() as conn:
        # This should reset my sqlite db
        await conn.run_sync(Base.metadata.drop_all)

    # Explicitly close all sessions and dispose of the engine to
    await engine.dispose()


SYNC_TEST_DB_URL = os.getenv("SYNC_TEST_DB_URL")

# if ASYNC_TEST_DB_URL is None:
#     raise ValueError("ASYNC_TEST_DB_URL environment variable is not set")

if SYNC_TEST_DB_URL is None:
    raise ValueError("SYNC_TEST_DB_URL environment variable is not set")


@pytest.fixture(scope="function")
def db_session_in_mem():
    # GPT recommended the name "regular_session, which was taken"
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)

    regular_maker = sessionmaker(bind=engine, expire_on_commit=False)

    try:
        yield regular_maker
    finally:
        # session.close()
        engine.dispose()


@pytest.fixture(scope="session")
def sync_engine(postgres_test_db):
    """Create a synchronous PostgreSQL engine shared across the test session."""
    if SYNC_TEST_DB_URL is None:
        raise ValueError("SYNC_TEST_DB_URL was None")

    test_engine = create_engine(
        SYNC_TEST_DB_URL,
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True,
    )

    # Create all tables
    Base.metadata.create_all(test_engine)

    try:
        yield test_engine
    finally:
        test_engine.dispose()


@pytest.fixture(scope="function")
def postgres_db_isolation(sync_engine):
    """Keep Postgres-backed tests isolated without recreating the database."""
    truncate_all_tables_via_engine(sync_engine)
    yield
    truncate_all_tables_via_engine(sync_engine)


@pytest.fixture(scope="function")
def regular_session_maker(sync_engine, postgres_db_isolation):
    """Create a synchronous session maker."""
    from sqlalchemy.orm import sessionmaker

    session_maker = sessionmaker(sync_engine, expire_on_commit=False)

    return session_maker
