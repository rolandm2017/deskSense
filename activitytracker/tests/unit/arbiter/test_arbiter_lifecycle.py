import math

from activitytracker.arbiter.activity_arbiter import ActivityArbiter
from activitytracker.arbiter.session_polling import KeepAliveEngine
from activitytracker.object.classes import ChromeSession, ProgramSession

from ...data.arbiter_events import test_sessions
from ...helper.confirm_chronology import get_durations_from_test_data
from ...helper.deepcopy_test_data import deepcopy_test_data
from ...mocks.fake_persistence import FakeSystemStatusDao
from ...mocks.mock_clock import MockClock
from ...mocks.mock_engine_container import DeterministicPulseContainer
from ...mocks.recording_activity_recorder import RecordingActivityRecorder


def _build_arbiter_with_recording_recorder(sessions):
    clock_times = [session.start_time.dt for session in sessions]
    clock = MockClock(clock_times)
    durations = [int(x) for x in get_durations_from_test_data(sessions)]
    pulse_container = DeterministicPulseContainer(durations + [0])
    arbiter = ActivityArbiter(clock, FakeSystemStatusDao(), pulse_container)
    recorder = RecordingActivityRecorder()
    arbiter.add_recorder_listener(recorder)
    return arbiter, recorder, durations


def test_arbiter_lifecycle_routes_sessions_using_recording_recorder():
    sessions = deepcopy_test_data(test_sessions[:4])
    arbiter, recorder, durations = _build_arbiter_with_recording_recorder(sessions)

    for session in sessions:
        arbiter.transition_state(session)

    assert len(recorder.new_sessions) == 4
    assert len(recorder.concluded_sessions) == 3
    assert len(recorder.partial_windows) == 3

    expected_full_windows = sum(math.floor(duration / 10) for duration in durations)
    assert len(recorder.full_windows) == expected_full_windows

    assert recorder.concluded_sessions[0].end_time == recorder.concluded_sessions[1].start_time
    assert recorder.concluded_sessions[1].end_time == recorder.concluded_sessions[2].start_time


def test_arbiter_lifecycle_mixed_program_and_chrome_sessions():
    sessions = deepcopy_test_data(test_sessions[:6])
    arbiter, recorder, durations = _build_arbiter_with_recording_recorder(sessions)

    for session in sessions:
        arbiter.transition_state(session)

    assert any(isinstance(session, ProgramSession) for session in recorder.new_sessions)
    assert any(isinstance(session, ChromeSession) for session in recorder.new_sessions)

    expected_full_windows = sum(
        KeepAliveEngine.compute_pulses(duration)[0] for duration in durations
    )
    assert len(recorder.full_windows) == expected_full_windows
    assert len(recorder.concluded_sessions) == len(sessions) - 1
