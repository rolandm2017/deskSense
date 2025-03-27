import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text



import warnings
import pytest

import sys
from pathlib import Path


from dotenv import load_dotenv
import os

from surveillance.src.db.models import Base




@pytest.fixture(autouse=True)
def ignore_resource_warnings():
    # TODO: actually get rid of the src of warnings
    # TODO: Claude told me to do this
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)


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





# TODO:
# if logging_dao.find_session(session):
#     print("weeeee 64ru")
#     await logging_dao.push_window_ahead_ten_sec(session)
# else:
#     print(" vvvvvvvvvvvvvvvv Here 66ru")
#     await logging_dao.start_session(session)



load_dotenv()

# Get the test database connection string
ASYNC_TEST_DB_URL = ASYNC_TEST_DB_URL = os.getenv(
    'ASYNC_TEST_DB_URL')

# Optional: Add error handling if the variable is required
if ASYNC_TEST_DB_URL is None:
    raise ValueError("TEST_DB_STRING environment variable is not set")


@pytest.fixture(scope="function")
async def async_engine():
    """Create an async PostgreSQL engine for testing"""
    # Create engine that connects to default postgres database
    if ASYNC_TEST_DB_URL is None:
        raise ValueError("ASYNC_TEST_DB_URL was None")
    default_url = ASYNC_TEST_DB_URL.rsplit('/', 1)[0] + '/postgres'
    admin_engine = create_async_engine(
        default_url,
        isolation_level="AUTOCOMMIT"
    )

    async with admin_engine.connect() as conn:
        # Terminate existing connections more safely
        await conn.execute(text("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = 'dsTestDb'
            AND pid <> pg_backend_pid()
        """))

        # Drop and recreate database
        await conn.execute(text("DROP DATABASE IF EXISTS dsTestDb"))
        await conn.execute(text("CREATE DATABASE dsTestDb"))

    await admin_engine.dispose()

    # Create engine for test database
    test_engine = create_async_engine(
        ASYNC_TEST_DB_URL,
        # echo=True,
        isolation_level="AUTOCOMMIT"
    )

    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        return test_engine
    finally:
        await test_engine.dispose()

        # Clean up by dropping test database
        admin_engine = create_async_engine(
            default_url,  # Connect to default db for cleanup
            isolation_level="AUTOCOMMIT"
        )
        async with admin_engine.connect() as conn:
            await conn.execute(text("""
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = 'dsTestDb'
                AND pid <> pg_backend_pid()
            """))
            await conn.execute(text("DROP DATABASE IF EXISTS dsTestDb"))
        await admin_engine.dispose()




@pytest_asyncio.fixture(scope="function")
async def async_session_maker(async_engine):
    """Create an async session maker"""
    # engine = await anext(async_engine)  # Use anext() instead of await
    engine = await async_engine  # Simply await the engine
    session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    return session_maker


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
def shutdown_session_maker(sync_engine):
    """Create a synchronous session maker"""
    from sqlalchemy.orm import sessionmaker

    session_maker = sessionmaker(
        sync_engine,
        expire_on_commit=False
    )

    # session_factory = sessionmaker(bind=sync_engine, expire_on_commit=False)

    # shutdown_session_maker = scoped_session(session_factory)
    return session_maker
