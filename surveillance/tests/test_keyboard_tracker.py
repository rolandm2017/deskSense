import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import tempfile
from pathlib import Path

from src.trackers.keyboard_tracker import KeyboardTrackerCore
from src.util.threaded_tracker import ThreadedTracker
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
        datetime(2025, 1, 1, 12, 0, 2),
        datetime(2025, 1, 1, 12, 0, 2),
        datetime(2025, 1, 1, 12, 0, 3),
        datetime(2025, 1, 1, 12, 0, 4),
        datetime(2025, 1, 1, 12, 0, 5)
    ]
    return MockClock(times)

@pytest.fixture
def mock_keyboard_facade():
    return MockKeyboardFacade()

@pytest.fixture
def event_collector():
    events = []
    
    def event_handler(event):
        print(event, len(events), "VVV In the handler, 51ru")
        events.append(event)
        
    return events, event_handler

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
    assert isinstance(tracker.session_data, list)
    assert tracker.time_of_last_terminal_out is not None

def test_key_press_tracking(tracker_and_events, mock_keyboard_facade):
    """Test that key presses are tracked correctly."""
    tracker = tracker_and_events[0]
    events = tracker_and_events[1]
    
    # Simulate a key press
    mock_keyboard_facade.set_event('a')
    tracker.run_tracking_loop()
    
    assert tracker.recent_count == 1
    assert len(events) == 1
    assert events[0] == 'a'

def test_multiple_key_presses(tracker_and_events, mock_keyboard_facade):
    """Test tracking of multiple key presses."""
    tracker = tracker_and_events[0]
    events = tracker_and_events[1]
    t1 = tracker.time_of_last_terminal_out
    # print(t1, '88ru')
    
    # Simulate multiple key presses
    keys = ['a', 'b', 'c', 'd', 'e']  # first five occur within same timespan in Clock
    for key in keys:
        mock_keyboard_facade.set_event(key)
        tracker.run_tracking_loop()
    t2 = tracker.time_of_last_terminal_out
    # print(t2, '96ru')
    assert tracker.recent_count == 5, "Recent count didn't pick up the exact number of keypresses"
    assert len(events) == 5, "Failed to record the right number of events"
    assert events == keys

def test_ctrl_c_handling(tracker_and_events, mock_keyboard_facade):
    """Test that Ctrl+C is handled correctly."""
    tracker = tracker_and_events[0]
    
    mock_keyboard_facade.set_event('ctrl+c')
    tracker.run_tracking_loop()
    
    assert mock_keyboard_facade.ctrl_c_triggered

def test_internal_clock_implementation(tracker_and_events, mock_keyboard_facade):
    """Test that the internal clock 'really works.'"""
    tracker = tracker_and_events[0]
    initial_time = tracker.time_of_last_terminal_out
    assert isinstance(initial_time, datetime), "Time of last terminal out wasn't a datetime"

    seconds_into_the_future = 4
    tracker.clock.advance_time(seconds_into_the_future)
    new_time = tracker.clock._current_time  # for testing purposes

    change_in_time = new_time - initial_time
    print(change_in_time, '124ru')
    # assert change_in_time == 4, "Advance into the future did not work"
    tracker.update_time(new_time)

    updated_time = tracker.time_of_last_terminal_out
    assert isinstance(updated_time, datetime)

    four_seconds_have_elapsed = tracker.clock.has_elapsed_since(updated_time, initial_time, seconds_into_the_future)
    assert four_seconds_have_elapsed

def test_multiple_handlers_are_called(tracker_and_events, mock_keyboard_facade):
    """Test that when multiple handlers are provided, they are all called."""
    tracker = tracker_and_events[0]
    handler1_calls = []
    handler2_calls = []
    
    def handler1(event):
        handler1_calls.append(event)
    
    def handler2(event):
        handler2_calls.append(event)
    
    tracker.event_handlers = [handler1, handler2]
    
    mock_keyboard_facade.set_event('x')
    tracker.run_tracking_loop()
    
    assert len(handler1_calls) == len(handler2_calls) == 1
    assert handler1_calls[0] == handler2_calls[0] == 'x'

def test_gather_session(tracker_and_events, mock_keyboard_facade):
    """Test that gather_session returns and clears session data."""
    tracker = tracker_and_events[0]
    
    # Simulate some key presses
    keys = ['a', 'b', 'c']
    for key in keys:
        mock_keyboard_facade.set_event(key)
        tracker.run_tracking_loop()
    
    session_data = tracker.gather_session()
    assert len(session_data) == 0  # Should be empty as we're not adding to session_data
    assert tracker.session_data == []  # Should be cleared

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
    tracker_core = KeyboardTrackerCore(mock_clock, mock_keyboard_facade, handler)
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