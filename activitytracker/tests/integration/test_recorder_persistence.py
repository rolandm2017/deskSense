from datetime import timedelta

import pytest

from activitytracker.arbiter.activity_recorder import ActivityRecorder
from activitytracker.util.const import SECONDS_PER_HOUR
from activitytracker.util.time_wrappers import UserLocalTime

from ..data.arbiter_events import test_sessions
from ..helper.deepcopy_test_data import deepcopy_test_data
from ..mocks.fake_persistence import (
    FakeChromeLoggingDao,
    FakeChromeSummaryDao,
    FakeMysteryMediaDao,
    FakeProgramLoggingDao,
    FakeProgramSummaryDao,
    FakeVideoLoggingDao,
    FakeVideoSummaryDao,
)


def _build_recorder_with_fakes():
    program_logging = FakeProgramLoggingDao()
    chrome_logging = FakeChromeLoggingDao()
    video_logging = FakeVideoLoggingDao()
    program_summary = FakeProgramSummaryDao()
    chrome_summary = FakeChromeSummaryDao()
    video_summary = FakeVideoSummaryDao()
    mystery_dao = FakeMysteryMediaDao()
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
    return {
        "recorder": recorder,
        "program_logging": program_logging,
        "chrome_logging": chrome_logging,
        "program_summary": program_summary,
        "chrome_summary": chrome_summary,
    }


def test_program_recorder_persistence_with_fake_daos():
    deps = _build_recorder_with_fakes()
    recorder = deps["recorder"]
    session = deepcopy_test_data([test_sessions[1]])[0]
    completed = session.to_completed(
        UserLocalTime(session.start_time.dt + timedelta(seconds=15))
    )
    completed.duration = timedelta(seconds=15)

    recorder.on_new_session(session)
    recorder.add_ten_sec_to_end_time(session)
    recorder.add_partial_window(5, session)
    recorder.on_state_changed(completed)

    logs = deps["program_logging"].read_all()
    summaries = deps["program_summary"].read_all()
    assert len(logs) == 1
    assert len(summaries) == 1
    assert logs[0].duration_in_sec == 15
    assert summaries[0].hours_spent == pytest.approx(15 / SECONDS_PER_HOUR)


def test_chrome_recorder_persistence_with_fake_daos():
    deps = _build_recorder_with_fakes()
    recorder = deps["recorder"]
    session = deepcopy_test_data([test_sessions[0]])[0]
    completed = session.to_completed(
        UserLocalTime(session.start_time.dt + timedelta(seconds=12))
    )
    completed.duration = timedelta(seconds=12)

    recorder.on_new_session(session)
    recorder.add_ten_sec_to_end_time(session)
    recorder.add_partial_window(2, session)
    recorder.on_state_changed(completed)

    logs = deps["chrome_logging"].read_all()
    summaries = deps["chrome_summary"].read_all()
    assert len(logs) == 1
    assert len(summaries) == 1
    assert logs[0].duration_in_sec == 12
    assert summaries[0].hours_spent == pytest.approx(12 / SECONDS_PER_HOUR)
