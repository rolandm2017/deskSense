# tests/integration/test_keep_alive.py
import pytest
from unittest.mock import  Mock, MagicMock
from datetime import  timedelta, datetime
import math

from surveillance.src.config.definitions import keep_alive_pulse_delay
from surveillance.src.arbiter.activity_arbiter import ActivityArbiter
from surveillance.src.arbiter.activity_recorder import ActivityRecorder
from surveillance.src.object.classes import ProgramSession, ChromeSession

from surveillance.src.arbiter.session_heartbeat import KeepAliveEngine

from surveillance.src.util.time_wrappers import UserLocalTime

from ..data.arbiter_events import test_sessions, times_for_system_clock, minutes_between_start_and_2nd_to_last, test_evenbts_elapsed_time_in_sec
from ..mocks.mock_clock import MockClock
from ..mocks.mock_engine_container import MockEngineContainer

from ..helper.confirm_chronology import assert_test_data_is_chronological_with_tz, get_durations_from_test_data


# It runs in a mock container
# It runs thru the test sessions from the test_arbiter.py file
# The outcomes intended are verified to be exactly what was intended.

@pytest.fixture
def dao_connection():
    # Create an event log
    events = []

    def event_handler(session):
        events.append(session)

    recorder_spy = MagicMock(spec_set=ActivityRecorder)
    recorder_spy.on_state_changed.side_effect = event_handler

    return recorder_spy


@pytest.fixture
def activity_arbiter_and_setup():
    """
    Pytest fixture that returns a fresh ActivityArbiter instance for each test.
    Mocks the dependencies to avoid actual database or system interactions.
    """

    assert_test_data_is_chronological_with_tz(test_sessions)

    durations = get_durations_from_test_data(test_sessions)

    # Mock dependencies
    clock = MockClock(times=times_for_system_clock)

    # Create mock UI components
    ui_layer = MagicMock()
    ui_layer.on_state_changed = Mock()

    # Create a new arbiter instance for this test
    ultrafast_interval_for_testing = 0.025  # usually is 1.0
    durations_as_int = [int(x) for x in durations]
    
    final_loop = 7  # keep it under 10 so there isn't a final pulse
    durations_as_int.append(final_loop)

    threaded_container = MockEngineContainer(durations_as_int, ultrafast_interval_for_testing)

def test_one_complete_run(dao_connection):
    session = ProgramSession("Foo")

    engine = KeepAliveEngine(session, dao_connection)
    durations_for_test = [63]
    threaded_container = MockEngineContainer(durations_for_test)

    threaded_container.add_first_engine(engine)

    threaded_container.start()
    threaded_container.stop()

    # -- assert

    assert dao_connection.add_ten_sec_to_end_time.call_count == 6
    assert dao_connection.deduct_duration.call_count == 1

    duration = dao_connection.deduct_duration.call_args_list[0][0][0]
    assert duration == 70 - 63


def test_five_runs(dao_connection):
    session = ProgramSession("Foo")

    engine = KeepAliveEngine(session, dao_connection)
    durations_for_test = [63, 0, 10, 9, 23]

    # 0 and 10, deduct 10
    # 9 deducts 1.
    # What deducts 0?
    # This code is broken.

    # 0 is secretly 10.
    # If it ends on 0, withdraw the window push that just happened.

    # 0 is a full window,
    # 10 is 2 full windows
    # 9 is 1 full window
    # 23 is 3 full windows
    # 
    # 63 -> 6, so one per full 10
    # 0 -> 0
    # 10 -> 1
    # 0 -> 0
    # 23 -> 2
    full_windows_per_session = [6, 0, 1, 0, 2]
    count_of_full_windows = sum(full_windows_per_session)
    count_of_deductions = [1, 1, 1, 1, 1]  # 9 is not deducted

    # Remember that, if this were development, on_new_session would add 10 sec
    # before any of this happened. So there's a free +10 per session before this occurs.
    threaded_container = MockEngineContainer(durations_for_test)

    threaded_container.add_first_engine(engine)

    threaded_container.start()
    threaded_container.stop()

    assert durations_for_test[0] // 10 == 6
    assert dao_connection.add_ten_sec_to_end_time.call_count == 6

    assert dao_connection.deduct_duration.call_count == 1

    for i in durations_for_test[1:]:
        engine = KeepAliveEngine(session, dao_connection)
        threaded_container.replace_engine(engine)
    
        threaded_container.start()
        threaded_container.stop()

    # -- assert

    for i in range(0, len(durations_for_test)):
        deductions = dao_connection.deduct_duration.call_args_list[i][0][0]
        # 10 - (x % 10) = deduction_amt
        assert deductions == 10 - (durations_for_test[i] % 10)

    assert dao_connection.deduct_duration.call_count == len(count_of_deductions)

    assert dao_connection.add_ten_sec_to_end_time.call_count == count_of_full_windows
    