import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, Mock

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import text
import asyncio

from zoneinfo import ZoneInfo
from datetime import datetime, timedelta, timezone


from dotenv import load_dotenv
import os

# FIXME:
# FIXME: Task was destroyed but it is pending! ``
# FIXME: Task was destroyed but it is pending! 
# FIXME:

from src.arbiter.activity_recorder import ActivityRecorder

from src.db.models import DomainSummaryLog, ProgramSummaryLog, Base


from src.db.dao.direct.program_summary_dao import ProgramSummaryDao
from src.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from src.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao

from src.object.classes import ProgramSessionData, ChromeSessionData

from src.util.errors import ImpossibleToGetHereError


timezone_for_test_data = ZoneInfo('America/New_York')

load_dotenv()

@pytest_asyncio.fixture(scope="function")
async def test_dao_instances(async_engine_and_asm):
    """Create the necessary DAO instances for session integrity testing"""
    engine, asm = async_engine_and_asm
    # Create the DAOs
    program_logging_dao = ProgramLoggingDao(asm)
    chrome_logging_dao = ChromeLoggingDao(asm)

    
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
async def clean_tables(async_engine_and_asm):
    """Clean tables before each test"""
    engine, _ = async_engine_and_asm
    # async_session_maker = await async_session_maker
    # Clean before test
    await truncate_test_tables(engine)
    
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
async def test_start_session(plain_asm, mock_session_data):
    """Test that start_session calls queue_item correctly"""
    # Arrange
    program_session, chrome_session = mock_session_data
    program_dao = ProgramLoggingDao(plain_asm)
    chrome_dao = ChromeLoggingDao(plain_asm)
    
    # Save original methods
    original_program_queue = program_dao.queue_item
    original_chrome_queue = chrome_dao.queue_item
    original_program_process = program_dao.process_queue
    original_chrome_process = chrome_dao.process_queue
    
    # Replace with mocks to avoid actual DB operations
    program_dao.queue_item = AsyncMock()
    chrome_dao.queue_item = AsyncMock()
    program_dao.process_queue = AsyncMock()
    chrome_dao.process_queue = AsyncMock()
    
    try:
        # Act
        await program_dao.start_session(program_session)
        await chrome_dao.start_session(chrome_session)
        
        # Assert
        program_dao.queue_item.assert_called_once()
        chrome_dao.queue_item.assert_called_once()
        
        # We're not calling process_queue() in this test
    finally:
        # Restore original methods without calling them
        program_dao.queue_item = original_program_queue
        chrome_dao.queue_item = original_chrome_queue
        program_dao.process_queue = original_program_process
        chrome_dao.process_queue = original_chrome_process

@pytest.mark.asyncio
async def test_find_session(plain_asm, mock_session_data):
    """Test find_session with direct database inserts"""
    # Arrange
    program_session, chrome_session = mock_session_data
    
    # Insert test data directly using SQLAlchemy without DAO queuing
    async with plain_asm() as session:
        try:
            # Create program record
            program_log = ProgramSummaryLog()
            program_log.program_name = program_session.window_title
            program_log.start_time = program_session.start_time.astimezone(timezone.utc)
            program_log.gathering_date = program_session.start_time.date()
            session.add(program_log)
            
            # Create domain record
            chrome_log = DomainSummaryLog()
            chrome_log.domain = chrome_session.domain
            chrome_log.start_time = chrome_session.start_time.astimezone(timezone.utc)
            chrome_log.gathering_date = chrome_session.start_time.date()
            session.add(chrome_log)
            
            # Commit the changes
            await session.commit()
        except Exception as e:
            await session.rollback()
            pytest.fail(f"Failed to insert test data: {e}")
    
    # Create DAOs for testing find_session
    program_dao = ProgramLoggingDao(plain_asm)
    chrome_dao = ChromeLoggingDao(plain_asm)
    
    # Mock process_queue to prevent hanging
    program_dao.process_queue = AsyncMock()
    chrome_dao.process_queue = AsyncMock()
    
    # Read data to verify insertion worked
    programs = await program_dao.read_all()
    domains = await chrome_dao.read_all()
    
    assert len(programs) == 1, "Expected one program record"
    assert len(domains) == 1, "Expected one domain record"
    
    # Test finding existing sessions
    program_found = await program_dao.find_session(program_session)
    chrome_found = await chrome_dao.find_session(chrome_session)
    
    # Test finding non-existent sessions
    whenever = datetime(2025, 3, 2, 12, 59, 0, tzinfo=timezone_for_test_data)
    nonexistent_program = ProgramSessionData()
    nonexistent_program.start_time = whenever
    nonexistent_chrome = ChromeSessionData()
    nonexistent_chrome.start_time = whenever
    
    dne_program = await program_dao.find_session(nonexistent_program)
    dne_chrome = await chrome_dao.find_session(nonexistent_chrome)
    
    # Assertions
    assert program_found is not None, "Program session should be found"
    assert chrome_found is not None, "Chrome session should be found"
    assert isinstance(program_found, ProgramSummaryLog)
    assert isinstance(chrome_found, DomainSummaryLog)
    assert dne_program is None, "Non-existent program should return None"
    assert dne_chrome is None, "Non-existent chrome session should return None"
    
    # Additional assertions if found
    assert isinstance(program_found, ProgramSummaryLog)
    assert isinstance(chrome_found, DomainSummaryLog)
    assert program_found.id is not None
    assert chrome_found.id is not None
    assert program_found.start_time == program_session.start_time.astimezone(timezone.utc)
    assert chrome_found.start_time == chrome_session.start_time.astimezone(timezone.utc)

@pytest.mark.asyncio
async def test_push_window_ahead(plain_asm, mock_session_data):
    """Test assumes there is an existing session, which the test can 'push the window forward' for."""
    program_session, chrome_session = mock_session_data
    program_dao = ProgramLoggingDao(plain_asm)
    chrome_dao = ChromeLoggingDao(plain_asm)
    
    program_log = None
    chrome_log = None
    # async with plain_asm() as session:
    #     try:
    #         # Create program record
    #         program_log = ProgramSummaryLog()
    #         program_log.program_name = program_session.window_title
    #         program_log.start_time = program_session.start_time.astimezone(timezone.utc)
    #         program_log.gathering_date = program_session.start_time.date()
    #         session.add(program_log)
            
    #         # Create domain record
    #         chrome_log = DomainSummaryLog()
    #         chrome_log.domain = chrome_session.domain
    #         chrome_log.start_time = chrome_session.start_time.astimezone(timezone.utc)
    #         chrome_log.gathering_date = chrome_session.start_time.date()
    #         session.add(chrome_log)
            
    #         # Commit the changes
    #         await session.commit()
    #     except Exception as e:
    #         await session.rollback()
    #         pytest.fail(f"Failed to insert test data: {e}")

    await program_dao.start_session(program_session)
    await chrome_dao.start_session(chrome_session)

      # Sleep for 0.1 seconds to let a process finish
    await asyncio.sleep(0.1)

    initial_write_of_program = await program_dao.find_session(program_session)
    initial_write_of_chrome = await chrome_dao.find_session(chrome_session)

    # Test setup conditions to make sure the test works
    assert isinstance(initial_write_of_program, ProgramSummaryLog)
    assert isinstance(initial_write_of_chrome, DomainSummaryLog)

    # Act
    await program_dao.push_window_ahead_ten_sec(initial_write_of_program)
    await chrome_dao.push_window_ahead_ten_sec(initial_write_of_chrome)

    # get it back out now & see if it changed
    pro_log = await program_dao.find_session(program_session)
    chro_log = await chrome_dao.find_session(chrome_session)

    # Assert
    assert pro_log.end_time == initial_write_of_program.end_time + timedelta(seconds=10), "Window push failed"
    assert chro_log.end_time == initial_write_of_chrome.end_time + timedelta(seconds=10), "Window push failed!"

@pytest.fixture
def nonexistent_session():
    session = ChromeSessionData()
    session.domain = "github.com"
    session.detail = "DeepSeek Chat Repository"
    session.start_time = datetime(2025, 1, 1, 1, 0, 0, 0)  # almost certainly doesn't exist
    session.end_time = datetime(2025, 1, 1, 1, 0, 0, 1)
    session.duration = timedelta(minutes=1)
    session.productive = True
    return session


@pytest.mark.asyncio
async def test_push_window_error(plain_asm, nonexistent_session):
    try:
        program_dao = ProgramLoggingDao(plain_asm)
        chrome_dao = ChromeLoggingDao(plain_asm)

        with pytest.raises(ImpossibleToGetHereError):
            await program_dao.push_window_ahead_ten_sec(nonexistent_session)
        with pytest.raises(ImpossibleToGetHereError):
            await chrome_dao.push_window_ahead_ten_sec(nonexistent_session)
    finally:
        await truncate_test_tables(plain_asm)


@pytest.mark.asyncio
async def test_finalize_log_error(plain_asm, nonexistent_session):
    try:
        program_dao = ProgramLoggingDao(plain_asm)
        chrome_dao = ChromeLoggingDao(plain_asm)

        with pytest.raises(ImpossibleToGetHereError):
            await program_dao.finalize_log(nonexistent_session)
        with pytest.raises(ImpossibleToGetHereError):
            await chrome_dao.finalize_log(nonexistent_session)
    finally:
        await truncate_test_tables(plain_asm)