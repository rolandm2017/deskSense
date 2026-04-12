from datetime import timedelta

import pytest

from activitytracker.arbiter.activity_recorder import ActivityRecorder
from activitytracker.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from activitytracker.db.dao.direct.mystery_media_dao import MysteryMediaDao
from activitytracker.db.dao.direct.program_summary_dao import ProgramSummaryDao
from activitytracker.db.dao.direct.video_summary_dao import VideoSummaryDao
from activitytracker.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from activitytracker.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from activitytracker.db.dao.queuing.video_logs_dao import VideoLoggingDao
from activitytracker.db.models import DailyProgramSummary
from activitytracker.tz_handling.time_formatting import (
    convert_to_utc,
    get_start_of_day_from_datetime,
)
from activitytracker.util.const import SECONDS_PER_HOUR
from activitytracker.util.time_wrappers import UserLocalTime

from ..data.arbiter_events import test_sessions
from ..helper.deepcopy_test_data import deepcopy_test_data


def _make_preexisting_summary(session, starting_hours):
    day_start_local = get_start_of_day_from_datetime(session.start_time.dt)
    day_start_utc = convert_to_utc(day_start_local)
    return DailyProgramSummary(
        exe_path_as_id=session.exe_path,
        process_name=session.process_name,
        program_name=session.window_title,
        hours_spent=starting_hours,
        gathering_date=day_start_utc,
        gathering_date_local=day_start_utc.replace(tzinfo=None),
    )


def test_recorder_adds_to_existing_summary(regular_session_maker):
    program_logging = ProgramLoggingDao(regular_session_maker)
    chrome_logging = ChromeLoggingDao(regular_session_maker)
    video_logging = VideoLoggingDao(regular_session_maker)
    program_summary = ProgramSummaryDao(program_logging, regular_session_maker)
    chrome_summary = ChromeSummaryDao(chrome_logging, regular_session_maker)
    video_summary = VideoSummaryDao(video_logging, regular_session_maker)
    mystery_dao = MysteryMediaDao(regular_session_maker)
    recorder = ActivityRecorder(
        program_logging,
        chrome_logging,
        video_logging,
        program_summary,
        chrome_summary,
        video_summary,
        mystery_dao,
        DEBUG=True,
    )

    session = deepcopy_test_data([test_sessions[1]])[0]
    completed = session.to_completed(
        UserLocalTime(session.start_time.dt + timedelta(seconds=15))
    )
    completed.duration = timedelta(seconds=15)

    preexisting = _make_preexisting_summary(session, starting_hours=1.0)
    program_summary.add_new_item(preexisting)

    recorder.on_new_session(session)
    recorder.add_ten_sec_to_end_time(session)
    recorder.add_partial_window(5, session)
    recorder.on_state_changed(completed)

    summaries = program_summary.read_all()
    logs = program_logging.read_all()

    assert len(summaries) == 1
    assert summaries[0].hours_spent == pytest.approx(1.0 + 15 / SECONDS_PER_HOUR)
    assert len(logs) == 1
