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

from surveillance.src.arbiter.activity_recorder import ActivityRecorder

from surveillance.src.db.models import DomainSummaryLog, ProgramSummaryLog, Base


from surveillance.src.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao

from surveillance.src.object.classes import ProgramSessionData, ChromeSessionData

from surveillance.src.util.errors import ImpossibleToGetHereError


timezone_for_test_data = ZoneInfo('America/New_York')

load_dotenv()

@pytest_asyncio.fixture(scope="function")
async def test_dao_instances(async_engine_and_asm, regular_session):
    """Create the necessary DAO instances for session integrity testing"""
    engine, asm = async_engine_and_asm
    # Create the DAOs
    program_logging_dao = ProgramLoggingDao(regular_session, asm)
    chrome_logging_dao = ChromeLoggingDao(regular_session, asm)

    
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
    print("truncating")
    await truncate_test_tables(engine)


@pytest.fixture
def mock_session_data():
    test_program_session = ProgramSessionData(
        "Ventrilo",
        "The Programmer's Hangout",
        start_time=datetime(2025, 2, 1, 1, 0, 4, 0, tzinfo=timezone_for_test_data),
        productive=False
    )

    test_chrome_session = ChromeSessionData(
        "chatgpt.com",
        "gpt Chat Repository",
        datetime(2025, 2, 1, 1, 0, 5, 0, tzinfo=timezone_for_test_data),
        duration_for_tests=timedelta(minutes=1),
        productive=True
    )

    return test_program_session, test_chrome_session

@pytest_asyncio.fixture
async def prepare_daos(regular_session, plain_asm):
    program_dao = ProgramLoggingDao(regular_session, plain_asm)
    chrome_dao = ChromeLoggingDao(regular_session, plain_asm)

    yield program_dao, chrome_dao

    await program_dao.cleanup()
    await chrome_dao.cleanup()

    
@pytest.mark.asyncio
async def test_start_session(prepare_daos, mock_session_data):
    """Test that start_session calls queue_item correctly"""
    # Arrange
    program_session, chrome_session = mock_session_data
    program_dao, chrome_dao = prepare_daos
        
    # Act
    program_dao.start_session(program_session)
    chrome_dao.start_session(chrome_session)
    
    # Assert
    # TODO: Find a way to assert here!
    assert 1 == 1  # TEMP
    


@pytest.mark.asyncio
async def test_find_session(prepare_daos, plain_asm, mock_session_data):
    """Test find_session with direct database inserts"""
    # ### Arrange
    program_session, chrome_session = mock_session_data
    program_dao, chrome_dao = prepare_daos

    # Test Setup conditions
    programs = program_dao.read_all()
    domains = chrome_dao.read_all()
    assert len(programs) == 0
    assert len(domains) == 0

    # 
    program_dao.start_session(program_session)
    chrome_dao.start_session(chrome_session)
    
    program_dao_queue = program_dao.process_queue
    chrome_dao_queue = chrome_dao.process_queue
    try:
        # Mock process_queue to prevent hanging
        program_dao.process_queue = AsyncMock()
        chrome_dao.process_queue = AsyncMock()
        
        # Read data to verify insertion worked
        programs = program_dao.read_all()
        domains = chrome_dao.read_all()
        
        assert len(programs) == 1, "Expected one program record; setup conditions not met"
        assert len(domains) == 1, "Expected one domain record; setup conditions not met"
        
        # ### Act 

        # Test finding existing sessions
        program_found = program_dao.find_session(program_session)
        chrome_found = chrome_dao.find_session(chrome_session)
        
        # Test finding non-existent sessions
        whenever = datetime(2025, 3, 2, 12, 59, 0, tzinfo=timezone_for_test_data)
        nonexistent_program = ProgramSessionData("", "", whenever)
        nonexistent_chrome = ChromeSessionData(domain="", detail="", start_time=whenever)
        
        dne_program = program_dao.find_session(nonexistent_program)
        dne_chrome = chrome_dao.find_session(nonexistent_chrome)
        
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
    finally:
        # Restore original methods without calling them    
        program_dao.queue_item = program_dao_queue
        chrome_dao.queue_item = chrome_dao_queue

# TODO: Manually drop the tables

@pytest.mark.asyncio
async def test_push_window_ahead(prepare_daos, mock_session_data):
    """Test assumes there is an existing session, which the test can 'push the window forward' for."""
    program_session, chrome_session = mock_session_data
    program_dao, chrome_dao = prepare_daos
    # chrome_dao = ChromeLoggingDao(plain_asm)
    
    print("WRITING\t\t", program_session.start_time)
    program_dao.start_session(program_session)
    chrome_dao.start_session(chrome_session)
    print("pro session\t\t", program_session.start_time)

    # FIXME: A timezone issue

    initial_write_of_program = program_dao.find_session(program_session)
    initial_write_of_chrome = chrome_dao.find_session(chrome_session)

    def convert_back_to_local_tz(session: ProgramSummaryLog | DomainSummaryLog, tz):
        utc_start_time_from_db = session.start_time
        converted_start_time = utc_start_time_from_db.astimezone(tz)
        session.start_time = converted_start_time
        return session

    initial_write_of_program = convert_back_to_local_tz(initial_write_of_program, timezone_for_test_data)
    initial_write_of_chrome = convert_back_to_local_tz(initial_write_of_chrome, timezone_for_test_data)

    # Test setup conditions to make sure the test works
    assert isinstance(initial_write_of_program, ProgramSummaryLog)
    assert isinstance(initial_write_of_chrome, DomainSummaryLog)

    # Still testing setup, confirm that it received an end time
    init_pro_log_end_time = initial_write_of_program.end_time
    init_chro_log_end_time = initial_write_of_chrome.end_time

    assert isinstance(init_pro_log_end_time, datetime)
    assert isinstance(init_chro_log_end_time, datetime)

    # ### Act
    print("init write of program \t", initial_write_of_program.start_time)
    print("end time \t\t", initial_write_of_program.end_time)
    program_dao.push_window_ahead_ten_sec(initial_write_of_program)
    chrome_dao.push_window_ahead_ten_sec(initial_write_of_chrome)

    # get it back out now & see if it changed
    pro_log = program_dao.find_session(program_session)
    chro_log = chrome_dao.find_session(chrome_session)
    assert pro_log is not None
    assert chro_log is not None
    print("end time \t\t", pro_log.end_time)

    # Assert
    assert pro_log.end_time != init_pro_log_end_time
    assert chro_log.end_time != init_chro_log_end_time
    
    assert pro_log.end_time == initial_write_of_program.end_time + timedelta(seconds=10), "Window push failed"
    assert chro_log.end_time == initial_write_of_chrome.end_time + timedelta(seconds=10), "Window push failed!"

@pytest.fixture
def nonexistent_session():
    nonexistent_time = datetime(2025, 1, 1, 1, 0, 0, 0)  # almost certainly doesn't exist
    session = ChromeSessionData(domain = "github.com", 
                                detail = "DeepSeek Chat Repository", 
                                start_time=nonexistent_time, 
                                end_time = datetime(2025, 1, 1, 1, 0, 0, 1), 
                                duration_for_tests=timedelta(minutes=1),
                                productive=True)
    return session

@pytest.mark.asyncio
async def test_finalize_log_error(prepare_daos, regular_session, plain_asm, nonexistent_session):
    program_dao, chrome_dao = prepare_daos
    
    # try:
    program_dao = ProgramLoggingDao(regular_session, plain_asm)
    chrome_dao = ChromeLoggingDao(regular_session, plain_asm)

    with pytest.raises(ImpossibleToGetHereError):
        await program_dao.finalize_log(nonexistent_session)
    with pytest.raises(ImpossibleToGetHereError):
        await chrome_dao.finalize_log(nonexistent_session)
    # finally:
    #     await truncate_test_tables(plain_asm)