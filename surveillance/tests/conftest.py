import pytest
import pytest_asyncio
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text

from collections import defaultdict


import warnings
import sys
from pathlib import Path
import psutil

from dotenv import load_dotenv
import os

import asyncio
import sys

# Force Windows to use the SelectEventLoop instead of ProactorEventLoop
# This needs to happen before any asyncio code runs
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from surveillance.src.db.models import Base




# FIXME: If this block below being commented out causes problems, then
# do as Claude says here: https://claude.ai/chat/c87b680d-ca6a-4a78-a7bd-9f4b3a0a1387
# @pytest.fixture(scope="session")
# def event_loop():
#     """Create an instance of the default event loop for each test session."""
#     policy = asyncio.get_event_loop_policy()
#     loop = policy.new_event_loop()
#     yield loop
#     loop.close()



####

pytest_plugins = ["pytest_asyncio"]

# @pytest.fixture(autouse=True)
# def ignore_resource_warnings():
#     """Claude told me to do this. Note the TODO below"""
#     # TODO: actually get rid of the src of warnings
    
#     warnings.filterwarnings("ignore", category=RuntimeWarning)
#     warnings.filterwarnings("ignore", category=DeprecationWarning)


# Fixture allegedly solves
# >       response = await async_client.get("http://127.0.0.1:8000/dashboard/timeline")
# E       AttributeError: 'async_generator' object has no attribute 'get'

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


pytest_plugins = ["pytest_asyncio"]

def pytest_configure(config):
    config.option.asyncio_default_fixture_loop_scope = "function"

#
# # Make the tests run fine on both Ubuntu AND Windows
#

# Get the absolute path to the project root
project_root = Path(__file__).absolute().parent

# Add both the project root and the src directory to the path
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Print paths for debugging
print(f"Project root added to path: {project_root}")
print(f"Sys path: {sys.path}")


load_dotenv()

ASYNC_TEST_DB_URL = ASYNC_TEST_DB_URL = os.getenv(
    'ASYNC_TEST_DB_URL')

if ASYNC_TEST_DB_URL is None:
    raise ValueError("TEST_DB_STRING environment variable is not set")

        
# @pytest_asyncio.fixture(scope="session")  
# # TODO: if performaance on tests is terribad, figure out how to use one session scoped engine
# @pytest.fixture(scope="session")
@pytest_asyncio.fixture(scope="function")
async def global_test_engine():
    """Create a single engine shared across all tests"""
    # Connect to default postgres db for setup
    default_url = ASYNC_TEST_DB_URL.rsplit('/', 1)[0] + '/postgres'
    admin_engine = create_async_engine(
        default_url,
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True,
        echo=False
    )
    
    # Clear and recreate test db
    async with admin_engine.begin() as conn:
        await conn.execute(text("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = 'dsTestDb'
            AND pid <> pg_backend_pid()
        """))
        await conn.execute(text("DROP DATABASE IF EXISTS dsTestDb"))
        await conn.execute(text("CREATE DATABASE dsTestDb"))
    
    await admin_engine.dispose()
    
    # Create a single engine for all tests
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
        yield test_engine
    finally:
        # Proper cleanup at the end of all tests
        await test_engine.dispose()
        # Force garbage collection
        import gc
        gc.collect()

@pytest_asyncio.fixture(scope="function")
async def async_engine_and_asm(global_test_engine):
    """Set up database for each test with isolation"""
    # Create fresh tables for this test
    async with global_test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create a fresh session maker for each test
    async_session_maker = async_sessionmaker(
        global_test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=True,
        autocommit=False
    )
    
    yield global_test_engine, async_session_maker
    
    # Clean up tables but not the engine
    async with global_test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

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
    session_maker: async_sessionmaker  = async_sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    yield engine, session_maker
    
    async with session_maker () as session:
        await session.rollback()
    
    # Teardown: drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

SYNC_TEST_DB_URL = os.getenv("SYNC_TEST_DB_URL")

# if ASYNC_TEST_DB_URL is None:
#     raise ValueError("ASYNC_TEST_DB_URL environment variable is not set")

if SYNC_TEST_DB_URL is None:
    raise ValueError("SYNC_TEST_DB_URL environment variable is not set")


@pytest.fixture(scope="function")
def sync_engine():
    """Create a synchronous PostgreSQL engine for testing"""
    # Create engine that connects to default postgres database
    if SYNC_TEST_DB_URL is None:
        raise ValueError("SYNC_TEST_DB_URL was None")

    from sqlalchemy import create_engine, text

    # Extract the default postgres database URL
    default_url = SYNC_TEST_DB_URL.rsplit('/', 1)[0] + '/postgres'
    admin_engine = create_engine(
        default_url,
        isolation_level="AUTOCOMMIT"
    )

    with admin_engine.connect() as conn:
        # Terminate existing connections more safely
        conn.execute(text("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = 'dsTestDb'
            AND pid <> pg_backend_pid()
        """))

        # Drop and recreate database
        conn.execute(text("DROP DATABASE IF EXISTS dsTestDb"))
        conn.execute(text("CREATE DATABASE dsTestDb"))

    admin_engine.dispose()

    # Create engine for test database
    test_engine = create_engine(
        # pool_pre_ping resolves a bug
        SYNC_TEST_DB_URL, isolation_level="AUTOCOMMIT", pool_pre_ping=True)

    # Create all tables
    with test_engine.begin() as conn:
        Base.metadata.create_all(conn)

    try:
        yield test_engine
    finally:
        test_engine.dispose()

        # Clean up by dropping test database
        admin_engine = create_engine(
            default_url,
            isolation_level="AUTOCOMMIT"
        )
        with admin_engine.connect() as conn:
            conn.execute(text("""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = 'dsTestDb'
                AND pid <> pg_backend_pid()
            """))
            conn.execute(text("DROP DATABASE IF EXISTS dsTestDb"))
        admin_engine.dispose()


@pytest.fixture(scope="function")
def regular_session(sync_engine):
    """Create a synchronous session maker. So-called because it *only* goes into a SystemStatusDAO."""
    from sqlalchemy.orm import sessionmaker

    session_maker = sessionmaker(
        sync_engine,
        expire_on_commit=False
    )

    return session_maker
