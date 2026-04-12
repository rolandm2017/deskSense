from datetime import timedelta

from activitytracker.arbiter.state_machine import StateMachine
from activitytracker.util.time_wrappers import UserLocalTime

from ...data.arbiter_events import test_sessions
from ...helper.deepcopy_test_data import deepcopy_test_data
from ...mocks.mock_clock import MockClock


def _copy_first_n_sessions(n):
    return deepcopy_test_data(test_sessions[:n])


def test_set_new_session_initialization_returns_none():
    session_a = _copy_first_n_sessions(1)[0]
    clock = MockClock([session_a.start_time.dt])
    state_machine = StateMachine(clock)

    result = state_machine.set_new_session(session_a)

    assert result is None
    assert state_machine.current_state is not None


def test_set_new_session_returns_concluded_with_duration():
    session_a, session_b = _copy_first_n_sessions(2)
    clock = MockClock([session_a.start_time.dt, session_b.start_time.dt])
    state_machine = StateMachine(clock)

    state_machine.set_new_session(session_a)
    concluded = state_machine.set_new_session(session_b)

    assert concluded is not None
    assert concluded.start_time == session_a.start_time
    assert concluded.end_time == session_b.start_time
    assert concluded.duration == session_b.start_time.dt - session_a.start_time.dt


def test_three_sessions_form_chain():
    session_a, session_b, session_c = _copy_first_n_sessions(3)
    clock = MockClock(
        [session_a.start_time.dt, session_b.start_time.dt, session_c.start_time.dt]
    )
    state_machine = StateMachine(clock)

    state_machine.set_new_session(session_a)
    concluded_a = state_machine.set_new_session(session_b)
    concluded_b = state_machine.set_new_session(session_c)

    assert concluded_a is not None
    assert concluded_b is not None
    assert concluded_a.end_time == concluded_b.start_time


def test_conclude_without_replacement_at_time_resets_state():
    session_a = _copy_first_n_sessions(1)[0]
    end_time = UserLocalTime(session_a.start_time.dt + timedelta(seconds=13))
    clock = MockClock([session_a.start_time.dt, end_time.dt])
    state_machine = StateMachine(clock)

    state_machine.set_new_session(session_a)
    concluded = state_machine.conclude_without_replacement_at_time(end_time)

    assert concluded is not None
    assert concluded.end_time == end_time
    assert concluded.duration == timedelta(seconds=13)
    assert state_machine.current_state is None
