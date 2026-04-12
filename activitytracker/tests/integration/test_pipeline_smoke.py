import pytest

from activitytracker.arbiter.activity_arbiter import ActivityArbiter
from activitytracker.arbiter.activity_recorder import ActivityRecorder
from activitytracker.util.const import SECONDS_PER_HOUR

from ..data.arbiter_events import test_sessions
from ..helper.confirm_chronology import get_durations_from_test_data
from ..helper.deepcopy_test_data import deepcopy_test_data
from ..mocks.fake_persistence import (
    FakeChromeLoggingDao,
    FakeChromeSummaryDao,
    FakeMysteryMediaDao,
    FakeProgramLoggingDao,
    FakeProgramSummaryDao,
    FakeSystemStatusDao,
    FakeVideoLoggingDao,
    FakeVideoSummaryDao,
)
from ..mocks.mock_clock import MockClock
from ..mocks.mock_engine_container import DeterministicPulseContainer


def test_pipeline_smoke_final_db_state_only():
    sessions = deepcopy_test_data(test_sessions[:5])
    durations = [int(x) for x in get_durations_from_test_data(sessions)]

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
        DEBUG=False,
    )

    clock = MockClock([session.start_time.dt for session in sessions])
    container = DeterministicPulseContainer(durations + [0])
    arbiter = ActivityArbiter(clock, FakeSystemStatusDao(), container)
    arbiter.add_recorder_listener(recorder)

    for session in sessions:
        arbiter.transition_state(session)

    expected_total_seconds = sum(durations)
    total_summary_hours = sum(
        summary.hours_spent for summary in program_summary.read_all() + chrome_summary.read_all()
    )
    total_summary_seconds = total_summary_hours * SECONDS_PER_HOUR

    total_log_seconds = sum(
        log.duration_in_sec for log in program_logging.read_all() + chrome_logging.read_all()
    )

    assert len(program_logging.read_all()) + len(chrome_logging.read_all()) == len(sessions)
    assert total_summary_seconds == pytest.approx(expected_total_seconds)
    assert total_log_seconds == pytest.approx(expected_total_seconds)
