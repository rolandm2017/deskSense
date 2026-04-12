import pytest

from activitytracker.arbiter.activity_arbiter import ActivityArbiter
from activitytracker.arbiter.activity_recorder import ActivityRecorder
from activitytracker.object.classes import ChromeSession, ProgramSession
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


def _find_matching_log(session, program_logging, chrome_logging):
    if isinstance(session, ProgramSession):
        return next(
            log
            for log in program_logging
            if log.exe_path_as_id == session.exe_path
            and log.program_name == session.window_title
            and log.start_time_local == session.start_time.dt
        )
    assert isinstance(session, ChromeSession)
    return next(
        log
        for log in chrome_logging
        if log.domain_name == session.domain and log.start_time_local == session.start_time.dt
    )


def _find_matching_summary(session, program_summary, chrome_summary):
    if isinstance(session, ProgramSession):
        return next(
            summary
            for summary in program_summary
            if summary.exe_path_as_id == session.exe_path
            and summary.program_name == session.window_title
        )
    assert isinstance(session, ChromeSession)
    return next(
        summary for summary in chrome_summary if summary.domain_name == session.domain
    )


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

    program_logs = program_logging.read_all()
    chrome_logs = chrome_logging.read_all()
    program_summaries = program_summary.read_all()
    chrome_summaries = chrome_summary.read_all()
    expected_summary_seconds = {}

    for index, session in enumerate(sessions[:-1]):
        expected_duration = durations[index]
        matching_log = _find_matching_log(session, program_logs, chrome_logs)
        assert matching_log.duration_in_sec == expected_duration

        if isinstance(session, ProgramSession):
            assert matching_log.exe_path_as_id == session.exe_path
            assert matching_log.program_name == session.window_title
        else:
            assert matching_log.domain_name == session.domain

        if isinstance(session, ProgramSession):
            key = ("program", session.exe_path)
        else:
            key = ("chrome", session.domain)
        expected_summary_seconds[key] = expected_summary_seconds.get(key, 0) + expected_duration

    for key, expected_seconds in expected_summary_seconds.items():
        kind, _ = key
        if kind == "program":
            target_session = next(
                session
                for session in sessions[:-1]
                if isinstance(session, ProgramSession) and session.exe_path == key[1]
            )
        else:
            target_session = next(
                session
                for session in sessions[:-1]
                if isinstance(session, ChromeSession) and session.domain == key[1]
            )
        matching_summary = _find_matching_summary(
            target_session, program_summaries, chrome_summaries
        )
        assert matching_summary.hours_spent == pytest.approx(expected_seconds / SECONDS_PER_HOUR)

    expected_total_seconds = sum(durations)
    total_summary_hours = sum(
        summary.hours_spent for summary in program_summaries + chrome_summaries
    )
    total_summary_seconds = total_summary_hours * SECONDS_PER_HOUR

    total_log_seconds = sum(
        log.duration_in_sec for log in program_logs + chrome_logs
    )

    assert len(program_logs) + len(chrome_logs) == len(sessions)
    assert total_summary_seconds == pytest.approx(expected_total_seconds)
    assert total_log_seconds == pytest.approx(expected_total_seconds)
