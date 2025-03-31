import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from src.arbiter.activity_recorder import ActivityRecorder

from src.db.dao.direct.program_summary_dao import ProgramSummaryDao
from src.db.dao.direct.chrome_summary_dao import ChromeSummaryDao

from src.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao

from src.object.classes import ProgramSessionData, ChromeSessionData

# Test implementations with proper session object instantiation

@pytest.fixture
def program_session():
    session = ProgramSessionData()
    session.window_title = "Visual Studio Code"
    session.detail = "main.py"
    session.start_time = datetime(2023, 1, 1, 12, 0, 0)
    session.end_time = datetime(2023, 1, 1, 12, 10, 0)
    session.duration = timedelta(minutes=10)
    session.productive = True
    return session

@pytest.fixture
def chrome_session():
    session = ChromeSessionData()
    session.domain = "github.com"
    session.detail = "DeepSeek Chat Repository"
    session.start_time = datetime(2023, 1, 1, 12, 0, 0)
    session.end_time = datetime(2023, 1, 1, 12, 5, 0)
    session.duration = timedelta(minutes=5)
    session.productive = True
    return session

@pytest.fixture
def mock_daos():
    return {
        'program_logging': AsyncMock(spec=ProgramLoggingDao),
        'chrome_logging': AsyncMock(spec=ChromeLoggingDao),
        'program_summary': AsyncMock(spec=ProgramSummaryDao),
        'chrome_summary': AsyncMock(spec=ChromeSummaryDao),
    }

@pytest.fixture
def mock_clock():
    clock = MagicMock()
    clock.today_start.return_value = "2023-01-01"
    return clock

@pytest.fixture
def activity_recorder(mock_daos, mock_clock):
    return ActivityRecorder(
        user_facing_clock=mock_clock,
        program_logging_dao=mock_daos['program_logging'],
        chrome_logging_dao=mock_daos['chrome_logging'],
        program_summary_dao=mock_daos['program_summary'],
        chrome_summary_dao=mock_daos['chrome_summary'],
    )

@pytest.mark.asyncio
async def test_on_state_changed_program(activity_recorder, mock_daos, program_session):
    await activity_recorder.on_state_changed(program_session)
    
    mock_daos['program_logging'].finalize_log.assert_awaited_once_with(program_session)
    mock_daos['chrome_logging'].finalize_log.assert_not_awaited()

@pytest.mark.asyncio
async def test_on_state_changed_chrome(activity_recorder, mock_daos, chrome_session):
    await activity_recorder.on_state_changed(chrome_session)
    
    mock_daos['chrome_logging'].finalize_log.assert_awaited_once_with(chrome_session)
    mock_daos['program_logging'].finalize_log.assert_not_awaited()


@pytest.mark.parametrize("session_exists", [True, False])
@pytest.mark.asyncio
async def test_update_or_create_log(activity_recorder, session_exists):
    logging_dao = AsyncMock()
    session = "test-session"

    logging_dao.find_session = AsyncMock(return_value=session_exists)

    update_or_create_log = activity_recorder.update_or_create_log  # Replace with actual class

    await update_or_create_log(logging_dao, session)

    if session_exists:
        logging_dao.push_window_ahead_ten_sec.assert_awaited_once_with(session)
        logging_dao.start_session.assert_not_called()
    else:
        logging_dao.push_window_ahead_ten_sec.assert_not_called()
        logging_dao.start_session.assert_awaited_once_with(session)

@pytest.mark.asyncio
async def test_add_ten_sec_program(activity_recorder, mock_daos, program_session):
    # Create a brand new mock (no shared state)
    chrome_logging_mock = AsyncMock(spec=ChromeLoggingDao)
    chrome_logging_mock.find_session.return_value = False  # Explicitly False
    
    # Replace the DAO in the recorder
    activity_recorder.chrome_logging_dao = chrome_logging_mock
    
    await activity_recorder.add_ten_sec_to_end_time(program_session)
    
    mock_daos['program_summary'].push_window_ahead_ten_sec.assert_awaited_once_with(program_session)
    mock_daos['program_logging'].find_session.assert_called_once_with(program_session)
    mock_daos['program_logging'].push_window_ahead_ten_sec.assert_awaited_once_with(program_session)

@pytest.mark.asyncio
async def test_add_ten_sec_chrome_new_session(activity_recorder, mock_daos, chrome_session):
    # Reset and configure the existing mock
    mock_daos['chrome_logging'].reset_mock()
    mock_daos['chrome_logging'].find_session.return_value = False  # Make sure it returns False
    start_session_mock = AsyncMock()
    mock_daos["chrome_logging"].start_session = start_session_mock
    
    push_mock_for_programs = AsyncMock()
    push_mock_for_chrome = AsyncMock()

    mock_daos["program_logging"].push_window_ahead_ten_sec = push_mock_for_programs
    mock_daos["chrome_logging"].push_window_ahead_ten_sec = push_mock_for_chrome

    # Spy on update_or_create_log:
    original_update_or_create_log = activity_recorder.update_or_create_log
    update_or_create_log_spy = AsyncMock(wraps=original_update_or_create_log)
    activity_recorder.update_or_create_log = update_or_create_log_spy

    
    # Act
    await activity_recorder.add_ten_sec_to_end_time(chrome_session)
    
    # Assert
    update_or_create_log_spy.assert_awaited_once_with(mock_daos["chrome_logging"], chrome_session)
    # Restore the original state of the recorder:
    activity_recorder.update_or_create_log = original_update_or_create_log
    
    start_session_mock.assert_awaited_once()
    
    push_mock_for_programs.assert_not_awaited()
    push_mock_for_chrome.assert_not_called()  # Because that's the "if session exists" path

    mock_daos['chrome_summary'].push_window_ahead_ten_sec.assert_awaited_once_with(chrome_session)
    mock_daos['chrome_logging'].find_session.assert_called_once_with(chrome_session)

@pytest.mark.asyncio
async def test_deduct_duration_program(activity_recorder, mock_daos, program_session, mock_clock):
    duration = 5  # seconds
    
    await activity_recorder.deduct_duration(duration, program_session)
    
    mock_daos['program_summary'].deduct_remaining_duration.assert_awaited_once_with(
        program_session, duration, "2023-01-01"
    )

@pytest.mark.asyncio
async def test_error_cases(activity_recorder):
    # Test invalid type
    with pytest.raises(TypeError):
        await activity_recorder.on_state_changed("not a session object")
    
    # Test missing end_time
    bad_session = ProgramSessionData()
    bad_session.window_title = "Bad Session"
    bad_session.start_time = datetime.now()
    bad_session.end_time = None
    bad_session.duration = timedelta(seconds=10)
    
    with pytest.raises(ValueError):
        await activity_recorder.on_state_changed(bad_session)
    
    # Test missing duration
    bad_session.end_time = datetime.now()
    bad_session.duration = None
    
    with pytest.raises(ValueError):
        await activity_recorder.on_state_changed(bad_session)