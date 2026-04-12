from datetime import datetime, timedelta

from activitytracker.arbiter.activity_recorder import ActivityRecorder
from activitytracker.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from activitytracker.db.dao.direct.mystery_media_dao import MysteryMediaDao
from activitytracker.db.dao.direct.program_summary_dao import ProgramSummaryDao
from activitytracker.db.dao.direct.video_summary_dao import VideoSummaryDao
from activitytracker.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from activitytracker.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from activitytracker.db.dao.queuing.video_logs_dao import VideoLoggingDao
from activitytracker.object.classes import ProgramSession
from activitytracker.tz_handling.time_formatting import (
    convert_to_utc,
    get_start_of_day_from_datetime,
)
from activitytracker.util.time_wrappers import UserLocalTime


def test_gathering_date_is_start_of_day_in_utc(regular_session_maker):
    program_logging = ProgramLoggingDao(regular_session_maker)
    chrome_logging = ChromeLoggingDao(regular_session_maker)
    video_logging = VideoLoggingDao(regular_session_maker)
    program_summary = ProgramSummaryDao(program_logging, regular_session_maker)
    chrome_summary = ChromeSummaryDao(chrome_logging, regular_session_maker)
    video_summary = VideoSummaryDao(video_logging, regular_session_maker)
    mystery_media = MysteryMediaDao(regular_session_maker)
    recorder = ActivityRecorder(
        program_logging,
        chrome_logging,
        video_logging,
        program_summary,
        chrome_summary,
        video_summary,
        mystery_media,
        DEBUG=True,
    )

    start_time = datetime.fromisoformat("2025-03-22T23:59:50-07:00")
    session = ProgramSession(
        exe_path="C:/apps/Code.exe",
        process_name="Code.exe",
        window_title="Visual Studio Code",
        detail="state_machine.py",
        start_time=UserLocalTime(start_time),
    )
    completed = session.to_completed(UserLocalTime(start_time + timedelta(seconds=15)))

    recorder.on_new_session(session)
    recorder.add_ten_sec_to_end_time(session)
    recorder.add_partial_window(5, session)
    recorder.on_state_changed(completed)

    logs = program_logging.read_all()
    summaries = program_summary.read_all()
    expected_gathering_date = convert_to_utc(get_start_of_day_from_datetime(start_time))

    assert len(logs) == 1
    assert len(summaries) == 1
    assert logs[0].gathering_date == expected_gathering_date
    assert summaries[0].gathering_date == expected_gathering_date
