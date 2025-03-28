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
from src.db.dao.program_logs_dao import ProgramLoggingDao
from src.db.dao.chrome_logs_dao import ChromeLoggingDao

from src.object.classes import ProgramSessionData, ChromeSessionData

from src.util.errors import ImpossibleToGetHereError


timezone_for_test_data = ZoneInfo('America/New_York')

load_dotenv()

@pytest_asyncio.fixture(scope="function")
async def test_dao_instances(plain_asm):
    """Create the necessary DAO instances for session integrity testing"""
    # Create the DAOs
    program_logging_dao = ProgramLoggingDao(plain_asm)
    chrome_logging_dao = ChromeLoggingDao(plain_asm)

    
    return {
        "program_logging_dao": program_logging_dao,
        "chrome_logging_dao": chrome_logging_dao,
    }

async def truncate_test_tables(async_engine):
    """Truncate all test tables directly"""
    # NOTE: IF you run the tests in a broken manner,
    # ####  the first run AFTER fixing the break
    # ####  MAY still look broken.
    # ####  Because the truncation happens *at the end of* a test.

    async with async_engine.begin() as conn:
        await conn.execute(text("TRUNCATE program_summary_logs RESTART IDENTITY CASCADE"))
        await conn.execute(text("TRUNCATE domain_summary_logs RESTART IDENTITY CASCADE"))
        await conn.execute(text("TRUNCATE system_change_log RESTART IDENTITY CASCADE"))
        print("Tables truncated")

@pytest_asyncio.fixture(autouse=True, scope="function")
async def clean_tables(async_engine):
    # async_session_maker = await async_session_maker
    """Clean tables before each test"""
    # Clean before test
    await truncate_test_tables(async_engine)
    
    # Run the test
    yield
    
    # # Clean after test
    # await truncate_test_tables(async_engine)


@pytest.fixture
def mock_session_data():
    test_program_session = ProgramSessionData()  
    test_program_session.window_title = "Ventrilo"
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
async def test_start_session(plain_asm, mock_session_data, async_engine):
    try: 
        # async_session_maker = await async_session_maker
        program_session, chrome_session = mock_session_data
        program_dao = ProgramLoggingDao(plain_asm)
        chrome_dao = ChromeLoggingDao(plain_asm)
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
        await truncate_test_tables(async_engine)
    
@pytest.mark.asyncio
async def test_find_session(plain_asm, mock_session_data, async_engine):
    try:
        program_session, chrome_session = mock_session_data

        program_dao = ProgramLoggingDao(plain_asm)
        chrome_dao = ChromeLoggingDao(plain_asm)

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

        await program_dao.start_session(program_session)
        await chrome_dao.start_session(chrome_session)

        # ### Test more setup conditions: The writes both worked

        programs = await program_dao.read_all()
        domains = await chrome_dao.read_all()

        queue_item_spy_programs.assert_called_once()
        queue_item_spy_chrome.assert_called_once()

        assert len(programs) == 1
        assert len(domains) == 1

        print(programs[0].start_time, "from db 215ru")
        # print(domains[0].start_time, "from db 216ru")

        print(program_session.start_time, "into db, 218ru")
        # print(chrome_session.start_time, "into db, 218ru")
        
        assert programs[0].start_time == program_session.start_time.astimezone(timezone.utc)
        assert domains[0].start_time == chrome_session.start_time.astimezone(timezone.utc)

        # ### Test some wild stuff
        assert isinstance(program_session.start_time, datetime)
        assert isinstance(chrome_session.start_time, datetime)

        whenever = datetime(2025, 3, 2, 12, 59, 0)
        nonexistent_program = ProgramSessionData()
        nonexistent_program.start_time = whenever
        nonexistent_chrome = ChromeSessionData()
        nonexistent_chrome.start_time = whenever

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

        assert program_log.start_time == program_session.start_time.astimezone(timezone.utc)
        assert chrome_log.start_time == chrome_session.start_time.astimezone(timezone.utc)
        
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
        await truncate_test_tables(async_engine)

@pytest.mark.asyncio
async def test_push_window_ahead(plain_asm, async_engine):
    program_dao = ProgramLoggingDao(plain_asm)
    chrome_dao = ChromeLoggingDao(plain_asm)
    

@pytest.mark.asyncio
async def test_start_session(plain_asm, async_engine):
    program_dao = ProgramLoggingDao(plain_asm)
    chrome_dao = ChromeLoggingDao(plain_asm)


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
# async def test_push_window_error(plain_asm):
#     try:
#         program_dao = ProgramLoggingDao(plain_asm)
#         chrome_dao = ChromeLoggingDao(plain_asm)

#         doesnt_exist = nonexistent_session()
#         with pytest.raises(ImpossibleToGetHereError):
#             program_dao.push_window_ahead_ten_sec(doesnt_exist)
#         with pytest.raises(ImpossibleToGetHereError):
#             chrome_dao.push_window_ahead_ten_sec(doesnt_exist)
#     finally:
#         await truncate_test_tables(plain_asm)


# @pytest.mark.asyncio
# async def test_finalize_log_error(plain_asm):
#     try:
#         program_dao = ProgramLoggingDao(plain_asm)
#         chrome_dao = ChromeLoggingDao(plain_asm)


#         doesnt_exist = nonexistent_session()
#         with pytest.raises(ImpossibleToGetHereError):
#             program_dao.finalize_log(doesnt_exist)
#         with pytest.raises(ImpossibleToGetHereError):
#             chrome_dao.finalize_log(doesnt_exist)
#     finally:
#         await truncate_test_tables(plain_asm)