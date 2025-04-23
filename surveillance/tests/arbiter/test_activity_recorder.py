import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from surveillance.src.arbiter.activity_recorder import ActivityRecorder

from surveillance.src.db.dao.direct.program_summary_dao import ProgramSummaryDao
from surveillance.src.db.dao.direct.chrome_summary_dao import ChromeSummaryDao

from surveillance.src.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao

from surveillance.src.object.classes import ProgramSession, ChromeSession
from surveillance.src.util.time_wrappers import UserLocalTime


# Test implementations with proper session object instantiation


@pytest.fixture
def program_session():
    return ProgramSession("C:/ProgramFiles/Code.exe", "Code.exe",
                          "Visual Studio Code",
                          "main.py",
                          datetime(2023, 1, 1, 12, 0, 0),
                          datetime(2023, 1, 1, 12, 10, 0),
                          True,
                          timedelta(minutes=10)
                          )


@pytest.fixture
def chrome_session():
    return ChromeSession(
        "github.com",
        "DeepSeek Chat Repository",
        datetime(2023, 1, 1, 12, 0, 0),
        datetime(2023, 1, 1, 12, 5, 0),
        productive=True,
        duration_for_tests=timedelta(minutes=5)
    )


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
    activity_recorder.on_state_changed(program_session)

    mock_daos['program_logging'].finalize_log.assert_called_once_with(
        program_session)
    mock_daos['chrome_logging'].finalize_log.assert_not_called()


@pytest.mark.asyncio
async def test_on_state_changed_chrome(activity_recorder, mock_daos, chrome_session):
    activity_recorder.on_state_changed(chrome_session)

    mock_daos['chrome_logging'].finalize_log.assert_called_once_with(
        chrome_session)
    mock_daos['program_logging'].finalize_log.assert_not_called()


@pytest.mark.asyncio
async def test_deduct_duration_program(activity_recorder, mock_daos, program_session, mock_clock):
    duration = 5  # seconds

    activity_recorder.deduct_duration(duration, program_session)

    mock_daos['program_summary'].deduct_remaining_duration.assert_called_once_with(
        program_session, duration, "2023-01-01"
    )


@pytest.mark.asyncio
async def test_error_cases(activity_recorder):
    # Test invalid type
    with pytest.raises(TypeError):
        await activity_recorder.on_state_changed("not a session object")

    # Test missing end_time
    bad_session = ProgramSession()
    bad_session.window_title = "Bad Session"
    bad_session.start_time = UserLocalTime(datetime.now())
    bad_session.end_time = None
    bad_session.duration = timedelta(seconds=10)

    with pytest.raises(ValueError):
        await activity_recorder.on_state_changed(bad_session)

    # Test missing duration
    bad_session.end_time = UserLocalTime(datetime.now())
    bad_session.duration = None

    with pytest.raises(ValueError):
        await activity_recorder.on_state_changed(bad_session)
