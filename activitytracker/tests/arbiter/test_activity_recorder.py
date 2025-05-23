import pytest
from unittest.mock import AsyncMock, MagicMock

import pytz
from datetime import datetime, timedelta

from activitytracker.arbiter.activity_recorder import ActivityRecorder
from activitytracker.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from activitytracker.db.dao.direct.mystery_media_dao import MysteryMediaDao
from activitytracker.db.dao.direct.program_summary_dao import ProgramSummaryDao
from activitytracker.db.dao.direct.video_summary_dao import VideoSummaryDao
from activitytracker.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from activitytracker.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from activitytracker.db.dao.queuing.video_logs_dao import VideoLoggingDao
from activitytracker.object.classes import (
    CompletedChromeSession,
    CompletedProgramSession,
)
from activitytracker.object.video_classes import NetflixInfo, VlcInfo
from activitytracker.util.time_wrappers import UserLocalTime

timezone_for_test = "Asia/Tokyo"  # UTC+9

tokyo_tz = pytz.timezone(timezone_for_test)


# Test implementations with proper session object instantiation

null_VLC_video_info = VlcInfo("9432432", "magic.mov", "C:/MagicContent", "playing")
null_netflix_info = NetflixInfo("Hilda", "23456", "playing")


@pytest.fixture
def program_session():
    return CompletedProgramSession(
        "C:/ProgramFiles/Code.exe",
        "Code.exe",
        "Visual Studio Code",
        "main.py",
        None,
        UserLocalTime(datetime(2023, 1, 1, 12, 0, 0, tzinfo=tokyo_tz)),
        UserLocalTime(datetime(2023, 1, 1, 12, 10, 0, tzinfo=tokyo_tz)),
        True,
        timedelta(minutes=10),
    )


@pytest.fixture
def chrome_session():
    return CompletedChromeSession(
        "github.com",
        "DeepSeek Chat Repository",
        None,
        UserLocalTime(datetime(2023, 1, 1, 12, 0, 0, tzinfo=tokyo_tz)),
        UserLocalTime(datetime(2023, 1, 1, 12, 5, 0, tzinfo=tokyo_tz)),
        productive=True,
        duration_for_tests=timedelta(minutes=5),
    )


@pytest.fixture
def mock_daos():
    return {
        "program_logging": AsyncMock(spec=ProgramLoggingDao),
        "chrome_logging": AsyncMock(spec=ChromeLoggingDao),
        "video_logging": AsyncMock(spec=VideoLoggingDao),
        "program_summary": AsyncMock(spec=ProgramSummaryDao),
        "chrome_summary": AsyncMock(spec=ChromeSummaryDao),
        "video_summary": AsyncMock(spec=VideoSummaryDao),
        "mystery_dao": AsyncMock(spec=MysteryMediaDao),
    }


@pytest.fixture
def mock_clock():
    clock = MagicMock()
    clock.today_start.return_value = "2023-01-01"
    return clock


@pytest.fixture
def activity_recorder(mock_daos, mock_clock):
    return ActivityRecorder(
        program_logging_dao=mock_daos["program_logging"],
        chrome_logging_dao=mock_daos["chrome_logging"],
        video_logging_dao=mock_daos["video_logging"],
        program_summary_dao=mock_daos["program_summary"],
        chrome_summary_dao=mock_daos["chrome_summary"],
        video_summary_dao=mock_daos["video_summary"],
        mystery_media_dao=mock_daos["mystery_dao"],
    )


@pytest.mark.asyncio
async def test_on_state_changed_program(activity_recorder, mock_daos, program_session):
    activity_recorder.on_state_changed(program_session)

    mock_daos["program_logging"].finalize_log.assert_called_once_with(program_session)
    mock_daos["chrome_logging"].finalize_log.assert_not_called()


@pytest.mark.asyncio
async def test_on_state_changed_chrome(activity_recorder, mock_daos, chrome_session):
    activity_recorder.on_state_changed(chrome_session)

    mock_daos["chrome_logging"].finalize_log.assert_called_once_with(chrome_session)
    mock_daos["program_logging"].finalize_log.assert_not_called()


@pytest.mark.asyncio
async def test_add_partial_window_program(activity_recorder, mock_daos, program_session):
    duration = 6  # seconds

    activity_recorder.add_partial_window(duration, program_session)

    start_of_day = program_session.start_time.dt.replace(hour=0, minute=0, second=0)

    mock_daos["program_summary"].add_used_time.assert_called_once_with(
        program_session, duration
    )
