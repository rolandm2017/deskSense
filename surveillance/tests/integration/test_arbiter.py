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
        system_clock=clock,
    )

    # Add UI listener
    arbiter.add_ui_listener(ui_layer.on_state_changed)

    # Create an event log
    program_events = []
    chrome_events = []

    # Create mock listeners with side effects to record calls
    mock_program_listener = MagicMock()
    mock_program_listener.on_program_session_completed = AsyncMock(
        side_effect=program_events.append)

    mock_chrome_listener = MagicMock()
    mock_chrome_listener.on_chrome_session_completed = AsyncMock(
        side_effect=chrome_events.append)

    # Example usage
    arbiter.add_program_summary_listener(mock_program_listener)
    arbiter.add_chrome_summary_listener(mock_chrome_listener)

    # Optionally mock the chrome service integration
    # mock_chrome_service = MagicMock()
    # mock_chrome_service.event_emitter.on = MagicMock()

    return arbiter, program_events, chrome_events, ui_layer


@pytest.mark.asyncio
async def test_activity_arbiter(activity_arbiter_and_setup):
    arbiter, program_events, chrome_events, ui_layer = activity_arbiter_and_setup

    # Setup: How much time should pass?
    expected_sum_of_time = 45 * 60  # 45 minutes, as per the arbiter_events.py file

    program_sessions_in_test = [
        item for item in test_sessions if isinstance(item, ProgramSessionData)]

    chrome_sessions_in_test = [
        item for item in test_sessions if isinstance(item, ChromeSessionData)]

    assert len(test_sessions) > 0, "Test setup failed"

    # ### Act
    for session in test_sessions:
        await arbiter.transition_state(session)

    # ### Assert

    # Elapsed time was as expected
    output_events = program_events + chrome_events

    assert len(program_events) > 0, "Not even one event made it"
    assert len(chrome_events) > 0, "Not even one event made it"

    assert all(isinstance(log, ProgramSessionData)
               for log in program_events), "A program event wasn't a program session"
    assert all(isinstance(log, ChromeSessionData)
               for log in chrome_events), "A Chrome event wasn't a Chrome session"

    for k in output_events:
        print(k.duration)

    assert any(isinstance(obj.duration, int) for obj in output_events) is False
    assert all(isinstance(obj.duration, timedelta) for obj in output_events)

    total = timedelta()
    for e in output_events:
        total = total + e.duration

    total_duration = total.total_seconds()

    assert expected_sum_of_time == total_duration
    # Total number of recorded Program DAO entries was as expected
    assert len(program_events) == len(
        program_sessions_in_test), "A program session didn't make it through"
    # Total number of recorded Chrome DAO Entries was as expected
    remaining_open_session_offset = 1
    assert len(chrome_events) == len(
        chrome_sessions_in_test) - remaining_open_session_offset, "A Chrome session didn't make it through"
    # UI notifier was called the expected number of times
    assert ui_layer.on_state_changed.call_count == len(test_sessions)

    # ### Check that they all received durations and end times
    assert all(log.end_time is not None for log in output_events)
    assert all(log.duration is not None for log in output_events)

    chronological = sorted(output_events, key=lambda obj: obj.start_time)

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
