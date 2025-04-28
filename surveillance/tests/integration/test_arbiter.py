# tests/integration/test_arbiter.py
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock, MagicMock
from datetime import datetime, date, timedelta, timezone

from surveillance.src.arbiter.activity_arbiter import ActivityArbiter
from surveillance.src.arbiter.activity_recorder import ActivityRecorder
from surveillance.src.object.classes import ProgramSession, ChromeSession

from surveillance.src.arbiter.session_heartbeat import KeepAliveEngine, ThreadedEngineContainer

from ..data.arbiter_events import test_sessions, times_for_system_clock, difference_between_start_and_2nd_to_last
from ..mocks.mock_clock import MockClock

# ###
# ##
# #  # Test the integrated arbiter with a series of somewhat realistic data
# ##
# ###

# FIXME: that test takes 13.17s   # Ben says 10ms for a full db setup and teardown


@pytest.fixture
def activity_arbiter_and_setup():
    """
    Pytest fixture that returns a fresh ActivityArbiter instance for each test.
    Mocks the dependencies to avoid actual database or system interactions.
    """
    # Mock dependencies
    clock = MockClock(times=times_for_system_clock)

    # Create mock UI components
    ui_layer = MagicMock()
    ui_layer.on_state_changed = Mock()

    # Create a new arbiter instance for this test
    ultrafast_interval_for_testing = 0.025  # usually is 1.0
    threaded_container = ThreadedEngineContainer(ultrafast_interval_for_testing)
    arbiter = ActivityArbiter(clock, threaded_container, KeepAliveEngine)

    # Add UI listener
    arbiter.add_ui_listener(ui_layer.on_state_changed)

    # Create an event log
    events = []

    def event_handler(session):
        events.append(session)

    # Create mock listeners with side effects to record calls

    # Use this pretty darn cool MagicMock(spec_set=whatever) thing
    recorder_spy = MagicMock(spec_set=ActivityRecorder)
    recorder_spy.on_state_changed.side_effect = event_handler
    # STILL HAS all the methods attached, as mocks
    # mock_activity_recorder = Mock()?
    # mock_activity_recorder.on_state_changed = Mock(
    #     side_effect=event_handler)

    arbiter.add_recorder_listener(recorder_spy)

    assert arbiter.activity_recorder == recorder_spy, "Test setup conditions failed"

    # Optionally mock the chrome service integration
    # mock_chrome_service = MagicMock()
    # mock_chrome_service.event_emitter.on = MagicMock()

    return arbiter, events, ui_layer, recorder_spy, ultrafast_interval_for_testing


def test_activity_arbiter(activity_arbiter_and_setup):
    arbiter, events_from_on_state_changed_handler, ui_layer, mock_activity_recorder, pulse_interval = activity_arbiter_and_setup

    # Setup: How much time should pass?
    expected_sum_of_time = 45 * 60  # 45 minutes, as per the arbiter_events.py file
    program_sessions_in_test = [
        item for item in test_sessions if isinstance(item, ProgramSession)]

    chrome_sessions_in_test = [
        item for item in test_sessions if isinstance(item, ChromeSession)]

    assert len(test_sessions) > 0, "Test setup failed"

    # ### Act
    counter = 0
    # Recommend using "-v --capture=no" to see logging,
    # as in "pytest .\tests\integration\test_arbiter.py -v --capture=no"
    for session in test_sessions:
        print(f"Loop iter {counter}")
        counter = counter + 1
        arbiter.transition_state(session)

    assert 1 == 1
    # ### ### Assert
    remaining_open_session_offset = 1

    # ### Test some basic assumptions

    assert len(
        events_from_on_state_changed_handler) > 0, "Not even one event made it"

    program_events = [
        e for e in events_from_on_state_changed_handler if isinstance(e, ProgramSession)]
    chrome_events = [
        e for e in events_from_on_state_changed_handler if isinstance(e, ChromeSession)]

    assert all(isinstance(log, ProgramSession)
               for log in program_events), "A program event wasn't a program session"
    assert all(isinstance(log, ChromeSession)
               for log in chrome_events), "A Chrome event wasn't a Chrome session"

    assert any(isinstance(obj.duration, int)
               for obj in events_from_on_state_changed_handler) is False
    assert all(isinstance(obj.duration, timedelta)
               for obj in events_from_on_state_changed_handler)

    # ### Test DAO notifications
    assert mock_activity_recorder.on_state_changed.call_count == len(
        # NOTE: Would be "- 1" if the final input was a ProgramSession
        program_sessions_in_test) + len(chrome_sessions_in_test) - remaining_open_session_offset
    # assert mock_activity_recorder.on_state_changed.call_count == len(
    # chrome_sessions_in_test) - remaining_open_session_offsetz

    # Total number of recorded Program DAO entries was as expected
    assert len(program_events) == len(
        program_sessions_in_test), "A program session didn't make it through"
    # Total number of recorded Chrome DAO Entries was as expected
    remaining_open_session_offset = 1
    assert len(chrome_events) == len(
        chrome_sessions_in_test) - remaining_open_session_offset, "A Chrome session didn't make it through"

    # ### Test UI Notification layer
    # UI notifier was called the expected number of times
    assert ui_layer.on_state_changed.call_count == len(test_sessions)

    # ### The total time elapsed is what was expected
    total = timedelta()
    for e in events_from_on_state_changed_handler:
        total = total + e.duration

    total_duration = total.total_seconds()

    assert expected_sum_of_time == total_duration

    # ### Check that sessions all received durations and end times
    assert all(
        log.end_time is not None for log in events_from_on_state_changed_handler), "An end time wasn't set"
    # FIXME: should also check that the duration is 10 sec despite the 0.1 sec pulse
    assert all(
        log.duration is not None for log in events_from_on_state_changed_handler), "A duration wasn't set"

    chronological = sorted(
        events_from_on_state_changed_handler, key=lambda obj: obj.start_time)

    # ### Assert the nth entry is concluded when the (n + 1)th entry starts

    for i in range(0, len(chronological)):
        is_last = i == len(chronological) - 1
        if is_last:
            break
        current = chronological[i]
        next = chronological[i + 1]
        duration_from_start_end_times = next.start_time - current.start_time
        assert current.end_time == next.start_time, "There was a misalignment in session start & end"
        assert current.duration == duration_from_start_end_times, "A duration did not calculate correctly"

    # Check that the Arbiter's test pulse did not
    # change the amount of time
    # in the sessions
    zero_index = 1
    one_still_in_arb = 1
    events_from_handler_len = len(test_sessions) - zero_index

    final_event_index = events_from_handler_len - 1

    assert len(events_from_on_state_changed_handler) == 13
    assert len(events_from_on_state_changed_handler) == events_from_handler_len

    # verify that test_sessions[14] is still lodged in the Arbiter.
    # Note that you have to match up the index of the one that is still in the arbiter
    # with it's position in test_sessions, while also accounting for zero index.
    # So as of this comment, the final test_session is number 14, meaning index 13, i.e. the final one.
    assert arbiter.state_machine.current_state.session.start_time == test_sessions[
        len(test_sessions) - 1].start_time

    t0 = events_from_on_state_changed_handler[0].start_time
    t13 = events_from_on_state_changed_handler[final_event_index].start_time

    sec_per_min = 60
    elapsed_time_in_test = (t13 - t0).total_seconds() / sec_per_min
    assert elapsed_time_in_test == difference_between_start_and_2nd_to_last, f"The elapsed time was not as expected, perhaps due to {pulse_interval} interval pulse"
