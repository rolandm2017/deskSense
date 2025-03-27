import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, Mock


from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text

from zoneinfo import ZoneInfo
from datetime import datetime, timedelta, timezone


from dotenv import load_dotenv
import os



from src.arbiter.activity_recorder import ActivityRecorder

from src.db.models import DomainSummaryLog, ProgramSummaryLog, Base


from src.db.dao.program_summary_dao import ProgramSummaryDao
from src.db.dao.chrome_summary_dao import ChromeSummaryDao
from src.db.dao.summary_logs_dao import ProgramLoggingDao, ChromeLoggingDao

from src.object.classes import ProgramSessionData, ChromeSessionData

from src.util.errors import ImpossibleToGetHereError


timezone_for_test_data = ZoneInfo('America/New_York')

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
        isolation_level="AUTOCOMMIT"  # Add this
    )

    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield test_engine
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


@pytest.fixture(scope="function")
async def async_session_maker(async_engine):
    """Create an async session maker"""
    engine = await anext(async_engine)  # Use anext() instead of await
    session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    return session_maker


@pytest_asyncio.fixture(scope="function")
async def test_dao_instances(async_session_maker):
    """Create the necessary DAO instances for session integrity testing"""
    # Create the DAOs
    program_logging_dao = ProgramLoggingDao(async_session_maker)
    chrome_logging_dao = ChromeLoggingDao(async_session_maker)

    
    return {
        "program_logging_dao": program_logging_dao,
        "chrome_logging_dao": chrome_logging_dao,
    }

async def truncate_test_tables(async_session_maker):
    """Truncate all test tables directly"""
    # NOTE: IF you run the tests in a broken manner,
    # ####  the first run AFTER fixing the break
    # ####  MAY still look broken.
    # ####  Because the truncation happens *at the end of* a test.

    async with async_session_maker.begin() as conn:
        await conn.execute(text("TRUNCATE program_summary_logs RESTART IDENTITY CASCADE"))
        await conn.execute(text("TRUNCATE domain_summary_logs RESTART IDENTITY CASCADE"))
        await conn.execute(text("TRUNCATE system_change_log RESTART IDENTITY CASCADE"))
        print("Tables truncated")


@pytest.fixture
def mock_session_data():
    test_program_session = ProgramSessionData()  
    test_program_session.window_title = "Discord"
    test_program_session.detail = "The Programmer's Hangout"
    test_program_session.start_time = datetime(2025, 2, 1, 1, 0, 4, 0, tzinfo=timezone_for_test_data)
    test_program_session.productive = False
    test_chrome_session = ChromeSessionData()
    test_chrome_session.domain = "chatgpt.com"
    test_chrome_session.detail = "gpt Chat Repository"
    test_chrome_session.start_time = datetime(2025, 2, 1, 1, 0, 5, 0, tzinfo=timezone_for_test_data)
    test_chrome_session.duration = timedelta(minutes=1)
    test_chrome_session.productive = True

    return test_program_session, test_chrome_session

@pytest.mark.asyncio
async def test_start_session(async_session_maker, mock_session_data):
    try: 
        async_session_maker = await async_session_maker
        program_session, chrome_session = mock_session_data
        program_dao = ProgramLoggingDao(async_session_maker)
        chrome_dao = ChromeLoggingDao(async_session_maker)
        queue_item_mock_program = AsyncMock()
        queue_item_mock_chrome = AsyncMock()
        program_dao.queue_item = queue_item_mock_program
        chrome_dao.queue_item = queue_item_mock_chrome

        # Act
        await program_dao.start_session(program_session)
        await chrome_dao.start_session(chrome_session)

        # Assert
        queue_item_mock_program.assert_called_once()
        queue_item_mock_chrome.assert_called_once()
    finally:
        await truncate_test_tables(async_session_maker)
    
@pytest.mark.asyncio
async def test_find_session(async_session_maker, mock_session_data):
    try:
        async_session_maker = await async_session_maker
        program_session, chrome_session = mock_session_data

        program_dao = ProgramLoggingDao(async_session_maker)
        chrome_dao = ChromeLoggingDao(async_session_maker)

        queue_item_spy_programs = Mock(side_effect=program_dao.queue_item)
        queue_item_spy_chrome = Mock(side_effect=chrome_dao.queue_item)
        program_dao.queue_item = queue_item_spy_programs
        chrome_dao.queue_item = queue_item_spy_chrome

        # queue_item_mock_program = AsyncMock()
        # queue_item_mock_chrome = AsyncMock()
        # program_dao.queue_item = queue_item_mock_program
        # chrome_dao.queue_item = queue_item_mock_chrome

        # Arrange (still)
        assert program_dao is not None
        assert chrome_dao is not None
        print(program_dao, '194ru')
        program_dao.start_session(program_session)
        chrome_dao.start_session(chrome_session)

        # Test more setup conditions: The writes both worked

        programs = await program_dao.read_all()
        domains = await chrome_dao.read_all()

        assert len(programs) == 1
        assert len(domains) == 1
        
        assert programs[0].start_time == program_session.start_time
        assert domains[0].start_time == chrome_session.start_time
        # assert programs[0].start_time.astimezone(timezone.utc) == program_session.start_time.astimezone(timezone.utc)
    
        # assert domains[0].start_time.astimezone(timezone.utc) == chrome_session.start_time.astimezone(timezone.utc)

        nonexistent_program = ProgramSessionData()
        nonexistent_chrome = ChromeSessionData()

        # Act
        dne_one = await program_dao.find_session(nonexistent_program)
        dne_two = await chrome_dao.find_session(nonexistent_chrome)

        program_log: ProgramSummaryLog = await program_dao.find_session(program_session)
        chrome_log: DomainSummaryLog = await chrome_dao.find_session(chrome_session)

        # Assert

        # The nonexistent ones
        assert dne_one is None
        assert dne_two is None

        # "Session found"
        assert program_log is not None
        assert chrome_log is not None
        assert isinstance(program_log, ProgramSummaryLog)
        assert isinstance(chrome_log, DomainSummaryLog)
        assert program_log.id is not None
        assert chrome_log.id is not None

        assert program_log.start_time == program_session.start_time
        assert chrome_log.start_time == chrome_session.start_time
        
        queue_item_spy_programs.assert_called_once()
        args, _ = queue_item_spy_programs.call_args
        assert len(args) == 2
        assert isinstance(args[0], ProgramSummaryLog)
        assert args[1] is ProgramSummaryLog  # Second arg should be the class itself

        
        queue_item_spy_chrome.assert_called_once()
        args, _ = queue_item_spy_chrome.call_args
        assert len(args) == 2
        assert isinstance(args[0], DomainSummaryLog)
        assert args[1] is DomainSummaryLog  # Second arg should be the class itself
    finally:
        await truncate_test_tables(async_session_maker)

@pytest.mark.asyncio
async def test_push_window_ahead(async_session_maker):
    async_session_maker = await async_session_maker
    program_dao = ProgramLoggingDao(async_session_maker)
    chrome_dao = ChromeLoggingDao(async_session_maker)
    

@pytest.mark.asyncio
async def test_start_session(async_session_maker):
    async_session_maker = await async_session_maker
    program_dao = ProgramLoggingDao(async_session_maker)
    chrome_dao = ChromeLoggingDao(async_session_maker)


@pytest.mark.asyncio
async def nonexistent_session():
    session = ChromeSessionData()
    session.domain = "github.com"
    session.detail = "DeepSeek Chat Repository"
    session.start_time = datetime(2025, 1, 1, 1, 0, 0, 0)  # almost certainly doesn't exist
    session.end_time = datetime(2025, 1, 1, 1, 0, 0, 1)
    session.duration = timedelta(minutes=1)
    session.productive = True
    return session


# @pytest.mark.asyncio
# async def test_push_window_error(async_session_maker):
#     async_session_maker = await async_session_maker
#     try:
#         program_dao = ProgramLoggingDao(async_session_maker)
#         chrome_dao = ChromeLoggingDao(async_session_maker)

#         doesnt_exist = nonexistent_session()
#         with pytest.raises(ImpossibleToGetHereError):
#             program_dao.push_window_ahead_ten_sec(doesnt_exist)
#         with pytest.raises(ImpossibleToGetHereError):
#             chrome_dao.push_window_ahead_ten_sec(doesnt_exist)
#     finally:
#         await truncate_test_tables(async_session_maker)


# @pytest.mark.asyncio
# async def test_finalize_log_error(async_session_maker):
#     async_session_maker = await async_session_maker
#     try:
#         program_dao = ProgramLoggingDao(async_session_maker)
#         chrome_dao = ChromeLoggingDao(async_session_maker)

#         doesnt_exist = nonexistent_session()
#         with pytest.raises(ImpossibleToGetHereError):
#             program_dao.finalize_log(doesnt_exist)
#         with pytest.raises(ImpossibleToGetHereError):
#             chrome_dao.finalize_log(doesnt_exist)
#     finally:
#         await truncate_test_tables(async_session_maker)