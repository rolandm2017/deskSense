# tests/integration/test_arbiter.py
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock, MagicMock
from datetime import datetime, date, timedelta, timezone

from src.arbiter.activity_arbiter import ActivityArbiter
from src.arbiter.activity_recorder import ActivityRecorder
from src.arbiter.activity_state_machine import ActivityStateMachine
from src.debug.ui_notifier import UINotifier
from src.object.classes import ProgramSessionData, ChromeSessionData

from ..data.arbiter_events import test_sessions, times_for_system_clock
from ..mocks.mock_clock import MockClock

# ###
# ##
# #  # Test the integrated arbiter with a series of somewhat realistic data
# ##
# ###


@pytest_asyncio.fixture
async def activity_arbiter_and_setup():
    """
    Pytest fixture that returns a fresh ActivityArbiter instance for each test.
    Mocks the dependencies to avoid actual database or system interactions.
    """
    # Mock dependencies
    clock = MockClock(times=times_for_system_clock)

    # Create mock UI components
    ui_layer = MagicMock()
    ui_layer.on_state_changed = AsyncMock()

    # Create a new arbiter instance for this test
    arbiter = ActivityArbiter(
        user_facing_clock=clock,
    )

    # Add UI listener
    arbiter.add_ui_listener(ui_layer.on_state_changed)

    # Create an event log
    events = []

    def event_handler(session, shutdown):
        events.append(session)

    # Create mock listeners with side effects to record calls
    mock_activity_recorder = AsyncMock()
    mock_activity_recorder.on_state_changed = AsyncMock(
        side_effect=event_handler)

    arbiter.add_summary_dao_listener(mock_activity_recorder)

    # Optionally mock the chrome service integration
    # mock_chrome_service = MagicMock()
    # mock_chrome_service.event_emitter.on = MagicMock()

    return arbiter, events, ui_layer, mock_activity_recorder


@pytest.mark.asyncio
async def test_activity_arbiter(activity_arbiter_and_setup):
    arbiter, events, ui_layer, mock_activity_recorder = activity_arbiter_and_setup

    # Setup: How much time should pass?
    expected_sum_of_time = 45 * 60  # 45 minutes, as per the arbiter_events.py file

    program_sessions_in_test = [
        item for item in test_sessions if isinstance(item, ProgramSessionData)]

    chrome_sessions_in_test = [
        item for item in test_sessions if isinstance(item, ChromeSessionData)]

    assert len(test_sessions) > 0, "Test setup failed"

    # TODO: Test the UINotifier
    # TODO: Test the DAO listeners

    # ### Act
    for session in test_sessions:
        await arbiter.transition_state(session)

    # ### ### Assert
    remaining_open_session_offset = 1

    # ### Test some basic assumptions

    assert len(events) > 0, "Not even one event made it"

    program_events = [e for e in events if isinstance(e, ProgramSessionData)]
    chrome_events = [e for e in events if isinstance(e, ChromeSessionData)]

    assert all(isinstance(log, ProgramSessionData)
               for log in program_events), "A program event wasn't a program session"
    assert all(isinstance(log, ChromeSessionData)
               for log in chrome_events), "A Chrome event wasn't a Chrome session"

    assert any(isinstance(obj.duration, int) for obj in events) is False
    assert all(isinstance(obj.duration, timedelta) for obj in events)

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
    for e in events:
        total = total + e.duration

    total_duration = total.total_seconds()

    assert expected_sum_of_time == total_duration

    # ### Check that sessions all received durations and end times
    assert all(log.end_time is not None for log in events)
    assert all(log.duration is not None for log in events)

    chronological = sorted(events, key=lambda obj: obj.start_time)

    # ### Assert the nth entry is concluded when the (n + 1)th entry starts

    for i in range(0, len(chronological)):
        is_last = i == len(chronological) - 1
        if is_last:
            break
        current = chronological[i]
        next = chronological[i + 1]
        duration = next.start_time - current.start_time
        assert current.end_time == next.start_time, "There was a misalignment in session start & end"
        assert current.duration == duration, "A duration did not calculate correctly"
