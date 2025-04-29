# tests/integration/test_keep_alive.py
import pytest
from unittest.mock import  Mock, MagicMock
from datetime import  timedelta, datetime
import math

from surveillance.src.config.definitions import keep_alive_pulse_delay
from surveillance.src.arbiter.activity_arbiter import ActivityArbiter
from surveillance.src.arbiter.activity_recorder import ActivityRecorder
from surveillance.src.object.classes import ProgramSession, ChromeSession

from surveillance.src.arbiter.session_polling import KeepAliveEngine

from surveillance.src.util.time_wrappers import UserLocalTime

from ..data.arbiter_events import test_sessions, minutes_between_start_and_2nd_to_last, test_evenbts_elapsed_time_in_sec
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


    # Create mock UI components
    ui_layer = MagicMock()
    ui_layer.on_state_changed = Mock()

    # Create a new arbiter instance for this test
    ultrafast_interval_for_testing = 0.025  # usually is 1.0
    durations_as_int = [int(x) for x in durations]
    
    final_loop = 7  # keep it under 10 so there isn't a final pulse
    durations_as_int.append(final_loop)

    return test_sessions, durations_as_int

def test_one_complete_run(dao_connection):
    session = ProgramSession("Foo")

    engine = KeepAliveEngine(session, dao_connection)
    durations_for_test = [63]
    engine_container = MockEngineContainer(durations_for_test)

    engine_container.add_first_engine(engine)

    engine_container.start()
    engine_container.stop()

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
    engine_container = MockEngineContainer(durations_for_test)

    engine_container.add_first_engine(engine)

    engine_container.start()
    engine_container.stop()

    assert durations_for_test[0] // 10 == 6
    assert dao_connection.add_ten_sec_to_end_time.call_count == 6

    assert dao_connection.deduct_duration.call_count == 1

    for i in durations_for_test[1:]:
        engine = KeepAliveEngine(session, dao_connection)
        engine_container.replace_engine(engine)
    
        engine_container.start()
        engine_container.stop()

    # -- assert

    for i in range(0, len(durations_for_test)):
        deductions = dao_connection.deduct_duration.call_args_list[i][0][0]
        # 10 - (x % 10) = deduction_amt
        assert deductions == 10 - (durations_for_test[i] % 10)

    assert dao_connection.deduct_duration.call_count == len(count_of_deductions)

    assert dao_connection.add_ten_sec_to_end_time.call_count == count_of_full_windows
    

def test_full_test_sessions(dao_connection, activity_arbiter_and_setup):
    tested_sessions, durations_between_sessions = activity_arbiter_and_setup

    window_pushes = 0
    pushes_by_index = {}
    deductions = []

    for index, duration in enumerate(durations_between_sessions):
        full_windows = duration // keep_alive_pulse_delay
        window_pushes += full_windows
        pushes_by_index[index] = full_windows

        deductions.append(duration % keep_alive_pulse_delay)


    expected_time = sum(durations_between_sessions)  # Remember 7 was added in setup

    engine = KeepAliveEngine(tested_sessions[0], dao_connection)
    
    # Remember that, if this were development, on_new_session would add 10 sec
    # before any of this happened. So there's a free +10 per session before this occurs.
    engine_container = MockEngineContainer(durations_between_sessions)
    
    engine_container.add_first_engine(engine)

    engine_container.start()
    engine_container.stop()

    for session in tested_sessions[1:]:
        engine = KeepAliveEngine(session, dao_connection)
        
        engine_container.replace_engine(engine)

        engine_container.start()
        engine_container.stop()

    assert dao_connection.add_ten_sec_to_end_time.call_count == window_pushes

    current_test_session_index = 0
    last = None
    success = 0

    def get_all_indexes_for_session(session):
        """Get all the add_ten_sec call indexes, so you can easily test them."""
        

    print(f"going for {window_pushes} in a row")
    # GPT: This is my second attempt at asserting
    for i in range(0, dao_connection.add_ten_sec_to_end_time.call_count):
        if last is None:
            # First iteration
            add_ten_sec_session = dao_connection.add_ten_sec_to_end_time.call_args_list[i][0][0]
            assert add_ten_sec_session.get_name() == tested_sessions[0].get_name()
            last = add_ten_sec_session
            success += 1
            continue
        # Section starts at i == 1
        add_ten_sec_session = dao_connection.add_ten_sec_to_end_time.call_args_list[i][0][0]
        session_hasnt_changed_yet = add_ten_sec_session.get_name() == last.get_name()
        if session_hasnt_changed_yet:
            print(f"asserting against {add_ten_sec_session.get_name()}")
            assert add_ten_sec_session.get_name() == tested_sessions[current_test_session_index].get_name()
            assert add_ten_sec_session.start_time.dt == tested_sessions[current_test_session_index].start_time.dt
            success += 1
            print(f"success: {success}")
            last = add_ten_sec_session
        else:
            print("Session changed")
            print(f"asserting against {add_ten_sec_session.get_name()}")
            current_test_session_index += 1
            assert add_ten_sec_session.get_name() == tested_sessions[current_test_session_index].get_name()
            assert add_ten_sec_session.start_time.dt == tested_sessions[current_test_session_index].start_time.dt
            success += 1
            last = add_ten_sec_session
            print(f"success: {success}")

        
    # GPT: This was my first attempt at asserting
    end_of_last_segment = 0
    for i in range(0, len(tested_sessions)):
        expected_windows = pushes_by_index[i]
        # Step through the expected windows in chunks
        for i in range(end_of_last_segment, expected_windows):
            add_ten_sec_session = dao_connection.add_ten_sec_to_end_time.call_args_list[i][0][0]
            assert add_ten_sec_session.get_name() == tested_sessions[i].get_name()
            assert add_ten_sec_session.start_time.dt == tested_sessions[i].start_time.dt
        end_of_last_segment = end_of_last_segment + expected_windows

        assert deductions[i] == dao_connection.deduct_duration.call_args_list[i][0][0]
        

