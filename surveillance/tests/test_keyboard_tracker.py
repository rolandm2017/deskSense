# test_keyboard_tracker.py
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from src.trackers.keyboard_tracker import KeyboardTrackerCore
from src.util.threaded_tracker import ThreadedTracker
from src.object.classes import KeyboardAggregate
from .mocks.mock_clock import MockClock


class MockKeyboardFacade:
    def __init__(self):
        self.current_event = None
        self.ctrl_c_triggered = False

    def read_event(self):
        return self.current_event

    def set_event(self, event):
        self.current_event = event

    def event_type_is_key_down(self, event):
        return event is not None

    def is_ctrl_c(self, event):
        return event == 'ctrl+c'

    def trigger_ctrl_c(self):
        self.ctrl_c_triggered = True


@pytest.fixture
def mock_clock():
    times = [
        datetime(2025, 1, 1, 12, 0, 0),
        datetime(2025, 1, 1, 12, 0, 1),
        datetime(2025, 1, 1, 12, 0, 1),
        datetime(2025, 1, 1, 12, 0, 1),
        datetime(2025, 1, 1, 12, 0, 1),
        datetime(2025, 1, 1, 12, 0, 2),
        datetime(2025, 1, 1, 12, 0, 3),
        datetime(2025, 1, 1, 12, 0, 8),
        datetime(2025, 1, 1, 12, 0, 9),
        datetime(2025, 1, 1, 12, 0, 12),
        datetime(2025, 1, 1, 12, 0, 15),
        datetime(2025, 1, 1, 12, 0, 16),
        datetime(2025, 1, 1, 12, 0, 17),
        datetime(2025, 1, 1, 12, 0, 18)
    ]
    return MockClock(times)


@pytest.fixture
def mock_keyboard_facade():
    return MockKeyboardFacade()


@pytest.fixture
def event_collector():
    handler_events = []

    def event_handler(event):
        handler_events.append(event)

    return handler_events, event_handler


@pytest.fixture
def tracker_and_events(mock_clock, mock_keyboard_facade, event_collector):
    events, handler = event_collector
    tracker = KeyboardTrackerCore(mock_clock, mock_keyboard_facade, handler)
    return tracker, events


def test_tracker_initialization(tracker_and_events):
    """Test that KeyboardTracker initializes correctly."""
    tracker = tracker_and_events[0]
    assert tracker.recent_count == 0
    assert isinstance(tracker.events, list)
    assert tracker.time_of_last_terminal_out is not None


def test_key_press_tracking(tracker_and_events, mock_keyboard_facade):
    """Test that key presses are tracked correctly."""
    tracker = tracker_and_events[0]
    handler_events = tracker_and_events[1]

    with patch.object(tracker.aggregator, 'add_event', wraps=tracker.aggregator.add_event) as mock_add_event:
        # Test a setup condition

        mock_keyboard_facade.set_event('A')
        tracker.run_tracking_loop()

        mock_keyboard_facade.set_event("B")
        tracker.run_tracking_loop()

        assert mock_add_event.call_count == 2
        # You can also check the specific calls if needed:
        call_args = [call[0][0] for call in mock_add_event.call_args_list]
        assert len(call_args) == 2

        # Simulate a key press
        mock_keyboard_facade.set_event('C')
        tracker.run_tracking_loop()

        # t1 = tracker.time_of_last_aggregator_update

        assert len(tracker.aggregator.current_aggregation.events) == 3
        assert tracker.recent_count == 3, "A B C is three events"
        assert len(
            handler_events) == 0, "Handler was called before aggregate closed"

        # Some fiddling
        n = 2
        tracker.clock.advance_time(n)

        mock_keyboard_facade.set_event("D")
        tracker.run_tracking_loop()

        # assert tracker.recent_count == 1, "D was after the window reset"
        assert len(handler_events) == 1, "Window closed by entry of 'd' char"

        # the char "d"
        assert len(tracker.aggregator.current_aggregation.events) == 1

        deliverable_for_db = handler_events[0]   # Note "events[0]"
        assert isinstance(deliverable_for_db, KeyboardAggregate)
        assert deliverable_for_db.session_start_time is not None
        assert deliverable_for_db.session_end_time is not None
        # assert all(isinstance(some_time, datetime) for some_time in my_times)

        #
        # Now, moving the clock forward two seconds (not one, but two)
        # will close the session with "D".
        #

        n = 3
        tracker.clock.advance_time(n)

        mock_keyboard_facade.set_event("I")
        tracker.run_tracking_loop()
        assert len(tracker.aggregator.current_aggregation.events) == 1
        assert len(handler_events) == 2

        tracker.clock.advance_time(1)

        mock_keyboard_facade.set_event("J")
        tracker.run_tracking_loop()
        mock_keyboard_facade.set_event("K")
        tracker.run_tracking_loop()

        assert len(tracker.aggregator.current_aggregation.events) == 2
        assert len(handler_events) == 3


def test_multiple_key_presses(tracker_and_events, mock_keyboard_facade):
    """Test tracking of multiple key presses."""
    tracker = tracker_and_events[0]
    events = tracker_and_events[1]

    t1_start = tracker.clock.now()
    assert isinstance(t1_start, datetime)

    # Simulate multiple key presses
    # first five occur within same timespan in Clock
    keys = ['a', 'b', 'c', 'd', 'e']
    for key in keys:
        mock_keyboard_facade.set_event(key)
        tracker.run_tracking_loop()

    mock_keyboard_facade.set_event("f")
    tracker.run_tracking_loop()  # Should close the aggregator loop

    assert isinstance(events[0], KeyboardAggregate)
    assert events[0].session_start_time is not None
    assert events[0].session_end_time is not None
    assert len(events) == 1


def test_ctrl_c_handling(tracker_and_events, mock_keyboard_facade):
    """Test that Ctrl+C is handled correctly."""
    tracker = tracker_and_events[0]

    mock_keyboard_facade.set_event('ctrl+c')
    tracker.run_tracking_loop()

    assert mock_keyboard_facade.ctrl_c_triggered


def test_multiple_handlers_are_called(tracker_and_events, mock_keyboard_facade):
    """Test that when multiple handlers are provided, they are all called."""
    tracker = tracker_and_events[0]
    handler1_calls = []
    handler2_calls = []

    def handler1(event):
        print("called 1 ", event)
        handler1_calls.append(event)

    def handler2(event):
        print("called 2 ", event)
        handler2_calls.append(event)

    tracker.event_handlers = [handler1, handler2]

    mock_keyboard_facade.set_event('x')
    tracker.run_tracking_loop()

    assert len(handler1_calls) == len(handler2_calls) == 0

    tracker.clock.advance_time(5)

    mock_keyboard_facade.set_event('y')
    tracker.run_tracking_loop()

    assert len(handler1_calls) == 1
    assert len(handler2_calls) == 1

    assert handler1_calls[0] == handler2_calls[0]


def test_end_program_routine_called(tracker_and_events):
    """Test that end program routine is called when stopping tracker."""
    tracker = tracker_and_events[0]
    end_program_called = []

    def mock_end_program(report):
        end_program_called.append(True)

    tracker.end_program_func = mock_end_program
    tracker.stop()

    assert len(end_program_called) == 1
    assert isinstance(tracker.generate_keyboard_report(), dict)


def test_threading_cleanup(mock_clock, mock_keyboard_facade, event_collector):
    """Test that ThreadedKeyboardTracker cleans up properly on stop."""
    events, handler = event_collector
    tracker_core = KeyboardTrackerCore(
        mock_clock, mock_keyboard_facade, handler)
    threaded_tracker = ThreadedTracker(tracker_core)

    threaded_tracker.start()
    assert threaded_tracker.is_running
    assert threaded_tracker.hook_thread.is_alive()

    threaded_tracker.stop()
    assert not threaded_tracker.is_running
    assert not threaded_tracker.hook_thread.is_alive()


def test_no_event_handling(tracker_and_events, mock_keyboard_facade):
    """Test that no events are processed when keyboard returns None."""
    tracker = tracker_and_events[0]
    events = tracker_and_events[1]

    mock_keyboard_facade.set_event(None)
    tracker.run_tracking_loop()

    assert tracker.recent_count == 0
    assert len(events) == 0
