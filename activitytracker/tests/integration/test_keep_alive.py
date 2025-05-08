# tests/integration/test_keep_alive.py
import pytest
import pytz
from unittest.mock import Mock, MagicMock
from datetime import timedelta, datetime
import math

from activitytracker.config.definitions import (
    keep_alive_cycle_length,
    window_push_length,
)
from activitytracker.arbiter.activity_recorder import ActivityRecorder
from activitytracker.object.classes import ProgramSession, ChromeSession

from activitytracker.arbiter.session_polling import KeepAliveEngine

from activitytracker.util.time_wrappers import UserLocalTime

from ..data.arbiter_events import (
    test_sessions,
    minutes_between_start_and_2nd_to_last,
    test_events_elapsed_time_in_sec,
)
from ..mocks.mock_clock import MockClock
from ..mocks.mock_engine_container import MockEngineContainer

from ..helper.polling_util import count_full_loops
from ..helper.confirm_chronology import (
    assert_test_data_is_chronological_with_tz,
    get_durations_from_test_data,
)


timezone_for_test = "Asia/Tokyo"  # UTC +9
tokyo_tz = pytz.timezone(timezone_for_test)


early_morning = tokyo_tz.localize(datetime(2025, 4, 1, 0, 0, 0))


class MockActivityRecorder:
    def __init__(self):
        # Initialize lists to track calls
        self.pulse_history = []
        self.partial_window_history = []

        # Create the mock objects with proper side effects
        self.on_new_session = Mock()
        self.on_state_changed = Mock()

        # Create add_ten_sec_to_end_time with side effect to record the pulse
        self.add_ten_sec_to_end_time = Mock()
        self.add_ten_sec_to_end_time.side_effect = self._record_pulse

        # Create add_partial_window with side effect to record the partial window
        self.add_partial_window = Mock()
        self.add_partial_window.side_effect = self._record_addition

    def _record_pulse(self, session):
        """Side effect function that records each pulse"""
        self.pulse_history.append(session)
        # Side effects in unittest.mock should return None by default
        return None

    def _record_addition(self, duration, session):
        """Side effect function that records each partial window"""
        self.partial_window_history.append((session, duration))
        # Side effects in unittest.mock should return None by default
        return None

    def get_session_key(self, session):
        """Create a unique key for each session based on name and start time"""
        return f"{session.get_name()}_{session.start_time.dt.isoformat()}"

    def get_pulse_count_for_session(self, session):
        """Return the count of pulses for a specific session"""
        session_key = self.get_session_key(session)
        count = 0
        for recorded_session in self.pulse_history:
            if self.get_session_key(recorded_session) == session_key:
                count += 1
        return count

    def get_pulse_sequence(self):
        """Return the sequence of session names that received pulses"""
        return [session.get_name() for session in self.pulse_history]

    def get_addition_for_session(self, session):
        """Return the partial window amount for a specific session"""
        session_key = self.get_session_key(session)
        for recorded_session, duration in self.partial_window_history:
            if self.get_session_key(recorded_session) == session_key:
                return duration
        return None

    def get_partial_window_history(self):
        """Return all partial windows in order with unique session identifiers"""
        return [
            (self.get_session_key(session), duration)
            for session, duration in self.partial_window_history
        ]

    def get_pulse_counts_by_session(self):
        """Return a dictionary of session names to pulse counts"""
        result = {}
        for session in self.pulse_history:
            name = session.get_name()
            result[name] = result.get(name, 0) + 1
        return result

    def get_pulse_counts_by_unique_session(self):
        """Return a dictionary of unique session keys to pulse counts"""
        result = {}
        for session in self.pulse_history:
            session_key = self.get_session_key(session)
            result[session_key] = result.get(session_key, 0) + 1
        return result


@pytest.fixture
def mock_recorder():
    """Fixture to provide the mock recorder"""
    return MockActivityRecorder()


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

    # final_loop = 7  # keep it under 10 so there isn't a final pulse
    # durations_as_int.append(final_loop)

    return test_sessions, durations_as_int


def test_one_complete_run(dao_connection):
    session = ProgramSession("Foo")

    engine = KeepAliveEngine(session, dao_connection)

    only_length = 63
    durations_for_test = [only_length]
    engine_container = MockEngineContainer(durations_for_test)

    engine_container.add_first_engine(engine)

    engine_container.start()
    engine_container.stop()

    # -- assert

    assert dao_connection.add_ten_sec_to_end_time.call_count == 6
    assert dao_connection.add_partial_window.call_count == 1

    duration = dao_connection.add_partial_window.call_args_list[0][0][0]
    assert duration == only_length % keep_alive_cycle_length == 3


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
    count_of_additions = [1, 1, 1, 1, 1]  # FIXME

    # Remember that, if this were development, on_new_session would add 10 sec
    # before any of this happened. So there's a free +10 per session before this occurs.
    engine_container = MockEngineContainer(durations_for_test)

    engine_container.add_first_engine(engine)

    engine_container.start()
    engine_container.stop()

    assert count_full_loops(durations_for_test[0]) == 6
    assert dao_connection.add_ten_sec_to_end_time.call_count == 6

    assert dao_connection.add_partial_window.call_count == 1

    for i in durations_for_test[1:]:
        engine = KeepAliveEngine(session, dao_connection)
        engine_container.replace_engine(engine)

        engine_container.start()
        engine_container.stop()

    # -- assert

    for i in range(0, len(durations_for_test)):
        if durations_for_test[i] % window_push_length == 0:
            continue  # Nothing to test
        partial_window = dao_connection.add_partial_window.call_args_list[i][0][0]
        assert partial_window == durations_for_test[i] % window_push_length

    assert dao_connection.add_partial_window.call_count == len(count_of_additions)

    assert dao_connection.add_ten_sec_to_end_time.call_count == count_of_full_windows


def test_full_test_sessions(activity_arbiter_and_setup, mock_recorder):
    tested_sessions, durations_between_sessions = activity_arbiter_and_setup

    window_pushes = 0
    pushes_by_index = {}
    partials = []

    for index, duration in enumerate(durations_between_sessions):
        full_windows = count_full_loops(duration)
        window_pushes += full_windows
        pushes_by_index[index] = full_windows

        partials.append(duration % keep_alive_cycle_length)

    expected_time = sum(durations_between_sessions)

    # Calculate expected results
    expected_pulses_by_session = {}
    expected_partials = {}

    def get_session_key(session):
        """Create a unique key for each session based on name and start time"""
        return f"{session.get_name()}_{session.start_time.dt.isoformat()}"

    for index, session in enumerate(tested_sessions):
        duration_exists_for_session = index < len(durations_between_sessions)
        # The final session has no duration, because there is session after it.
        if duration_exists_for_session:
            session_key = get_session_key(session)

            # Calculate full windows (each window is 10 seconds)
            full_windows = count_full_loops(durations_between_sessions[index])
            expected_pulses_by_session[session_key] = full_windows

            # Calculate expected partial (used bit of window)
            used_amount = durations_between_sessions[index] % keep_alive_cycle_length
            expected_partials[session_key] = used_amount if used_amount > 0 else None

    engine = KeepAliveEngine(tested_sessions[0], mock_recorder)

    # Remember that, if this were development, on_new_session would add 10 sec
    # before any of this happened. So there's a free +10 per session before this occurs.
    engine_container = MockEngineContainer(durations_between_sessions)

    for index, session in enumerate(tested_sessions):
        print(f"using session {session.get_name()} in index {index}")
        engine = KeepAliveEngine(session, mock_recorder)

        if index == 0:
            engine_container.add_first_engine(engine)
        else:
            engine_container.replace_engine(engine)

        engine_container.start()
        engine_container.stop()

        if engine_container.engine:
            if index == len(tested_sessions) - 1:
                # Nothing to assert for the final one
                break
            session_key = get_session_key(session)
            if expected_partials[session_key] is None:
                assert engine.amount_used == 0
            else:
                assert engine.amount_used == expected_partials[session_key]

    assert engine_container.count == len(tested_sessions) - 1
    assert mock_recorder.add_ten_sec_to_end_time.call_count == window_pushes

    # Debugging information
    print(f"Expected pulses: {expected_pulses_by_session}")
    print(f"Pulse history length: {len(mock_recorder.pulse_history)}")

    # Easier check - total pulse count
    total_expected_pulses = sum(expected_pulses_by_session.values())
    total_actual_pulses = len(mock_recorder.pulse_history)
    assert (
        total_actual_pulses == total_expected_pulses
    ), f"Expected {total_expected_pulses} total pulses but got {total_actual_pulses}"

    # Verify pulse counts for each session by unique key
    def assert_pulse_counts_were_as_expected():
        for session in tested_sessions:
            session_key = get_session_key(session)
            if session_key in expected_pulses_by_session:
                expected = expected_pulses_by_session[session_key]
                actual = mock_recorder.get_pulse_count_for_session(session)
                assert (
                    actual == expected
                ), f"Session {session.get_name()} (start: {session.start_time.dt.isoformat()}) expected {expected} pulses but got {actual}"

    assert_pulse_counts_were_as_expected()

    # Total partials count
    def assert_partials_were_all_counted():
        """Even the fake partials where elapsed_time == 0."""
        expected_partial_count = sum(1 for v in expected_partials.values())
        actual_partial_count = len(mock_recorder.partial_window_history) - 1
        assert (
            actual_partial_count == expected_partial_count
        ), f"Expected {expected_partial_count} partials but got {actual_partial_count}"

    assert_partials_were_all_counted()

    def assert_final_partial_is_from_final_test_data():
        assert (
            mock_recorder.partial_window_history[-1][0].get_name()
            == test_sessions[-1].get_name()
        )

    assert_final_partial_is_from_final_test_data()

    # Assert that the number of nonzero entries is the same

    # Verify partials for each session by unique key
    def assert_recorder_received_expected_partials():
        for session in tested_sessions:
            session_key = get_session_key(session)
            expected = expected_partials.get(session_key)
            if expected is not None:
                actual = mock_recorder.get_addition_for_session(session)
                assert (
                    actual == expected
                ), f"Session {session.get_name()} (start: {session.start_time.dt.isoformat()}) expected partial addition of {expected} but got {actual}"
            else:
                # Verify that it's a session that had x % 10 == 0 loops.
                actual_addition = mock_recorder.get_addition_for_session(session)
                assert actual_addition == 0

    assert_recorder_received_expected_partials()


def test_session_sequences_with_explicit_expectations():
    """
    Test a sequence of sessions with explicit expectations for
    pulses and partials, handling repeated application names.
    """
    # Create the mock recorder with side effects
    mock_recorder = MockActivityRecorder()

    # Helper function to generate unique session keys
    def get_session_key(session):
        return f"{session.get_name()}_{session.start_time.dt.isoformat()}"

    # Create test sessions that mimic your real test data
    t1 = tokyo_tz.localize(datetime(2023, 1, 1, 10, 0, 0))
    t2 = tokyo_tz.localize(datetime(2023, 1, 1, 10, 0, 30))
    t3 = tokyo_tz.localize(datetime(2023, 1, 1, 10, 1, 15))
    t4 = tokyo_tz.localize(datetime(2023, 1, 1, 10, 1, 45))
    t5 = tokyo_tz.localize(datetime(2023, 1, 1, 10, 2, 10))

    sessions = [
        # Create the right type of session object based on your actual code
        ProgramSession(
            "App1", "app1.exe", "App1", "First App", UserLocalTime(t1), productive=True
        ),
        ProgramSession(
            "App2", "app2.exe", "App2", "Second App", UserLocalTime(t2), productive=True
        ),
        ProgramSession(
            "App1",
            "app1.exe",
            "App1",
            "First App Again",
            UserLocalTime(t3),
            productive=True,
        ),  # Same app as #1
        ProgramSession(
            "App3", "app3.exe", "App3", "Third App", UserLocalTime(t4), productive=True
        ),
        ProgramSession(
            "App2",
            "app2.exe",
            "App2",
            "Second App Again",
            UserLocalTime(t5),
            productive=True,
        ),  # Same app as #2
    ]

    # Define explicit durations between sessions
    durations = [
        30,  # App1 runs for 30 seconds (3 full pulses)
        45,  # App2 runs for 45 seconds (4 full pulses, 5 sec partial)
        30,  # App1 runs for 30 seconds (3 full pulses)
        25,  # App3 runs for 25 seconds (2 full pulses, 5 sec partial)
        20,  # App2 runs for 20 seconds (2 full pulses)
    ]

    # Calculate expected pulses and partials
    expected_pulses = {}
    expected_partials = {}

    for i, session in enumerate(sessions):
        session_key = get_session_key(session)
        # Calculate full windows (each window is 10 seconds)
        full_windows = count_full_loops(durations[i])
        expected_pulses[session_key] = full_windows

        # Calculate expected partial (used_amount of window)
        used_amount = durations[i] % 10
        expected_partials[session_key] = used_amount

    # Run the test with the mock container
    engine_container = MockEngineContainer(durations)

    # Process each session
    for i, session in enumerate(sessions):
        engine = KeepAliveEngine(session, mock_recorder)

        if i == 0:
            engine_container.add_first_engine(engine)
        else:
            engine_container.replace_engine(engine)

        engine_container.start()
        engine_container.stop()

    # Debugging
    print(f"Expected pulses: {expected_pulses}")
    print(f"Pulse history length: {len(mock_recorder.pulse_history)}")

    # Verify overall pulse count
    total_expected_pulses = sum(expected_pulses.values())
    total_actual_pulses = len(mock_recorder.pulse_history)
    assert (
        total_actual_pulses == total_expected_pulses
    ), f"Expected {total_expected_pulses} total pulses but got {total_actual_pulses}"

    # Verify pulse counts for each session
    def assert_each_session_had_expected_pulse_count():
        for i, session in enumerate(sessions):
            session_key = get_session_key(session)
            expected_count = expected_pulses.get(session_key, 0)
            actual_count = mock_recorder.get_pulse_count_for_session(session)
            assert (
                actual_count == expected_count
            ), f"Session {session.get_name()} (start: {session.start_time.dt.isoformat()}) expected {expected_count} pulses but got {actual_count}"

    assert_each_session_had_expected_pulse_count()

    # Verify partials
    def assert_each_session_had_expected_partials():
        for i, session in enumerate(sessions):
            session_key = get_session_key(session)
            expected_partial = expected_partials.get(session_key)
            if expected_partial != 0:
                actual_partial = mock_recorder.get_addition_for_session(session)
                assert (
                    actual_partial == expected_partial
                ), f"Session {session.get_name()} (start: {session.start_time.dt.isoformat()}) expected partial of {expected_partial} but got {actual_partial}"
            else:
                actual_partial = mock_recorder.get_addition_for_session(session)
                assert actual_partial == 0, "Session ended on a full window"

    assert_each_session_had_expected_partials()
