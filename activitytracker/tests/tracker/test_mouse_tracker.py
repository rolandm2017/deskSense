# t ests/test_mouse_tracker.py
from annotated_types import T
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from datetime import datetime, timedelta

from activitytracker.util.detect_os import OperatingSystemInfo
from activitytracker.util.threaded_tracker import ThreadedTracker
from activitytracker.trackers.mouse_tracker import MouseTrackerCore, MouseEvent

# from activitytracker.facade.mouse_facade import MouseCoords


class MockMouseFacade:
    def __init__(self):
        # self.cursor_pos = MouseCoords(0, 0)
        self.hook_thread = None
        self.available = []

    def set_cursor_pos(self, pos):
        self.available.append(pos)

    def stop(self):
        print("Stopping fake facade")

    def get_all_events(self):
        temp = self.available
        self.available = []
        return temp

    def populate_event(self, event):
        self.available.append(event)


@pytest.fixture
def mock_mouse_facade():
    """Create a mock mouse API facade."""
    return MockMouseFacade()


@pytest.fixture
def event_collector():
    """Creates a collector and handler for mouse events"""
    events = []

    def event_handler(event):
        events.append(event)

    return events, event_handler


@pytest.fixture
def tracker_and_events(mock_mouse_facade, event_collector):
    """Create a MouseTracker instance with mocked dependencies."""
    events, handler = event_collector

    print("Stopping tracker")

    tracker = MouseTrackerCore(mock_mouse_facade, handler)

    yield tracker, events

    print("Stopping tracker")

    tracker.stop()


def test_make_sure_handler_actually_handles(tracker_and_events, mock_mouse_facade):
    tracker = tracker_and_events[0]
    events = tracker_and_events[1]

    now = datetime.now() - timedelta(hours=1)
    t1 = now + timedelta(milliseconds=5)
    t2 = t1 + timedelta(milliseconds=5)
    t3 = t2 + timedelta(milliseconds=5)
    t4 = t3 + timedelta(milliseconds=35)
    t5 = t4 + timedelta(milliseconds=1105)
    t6 = t5 + timedelta(milliseconds=135)
    t7 = t6 + timedelta(milliseconds=1205)
    t8 = t7 + timedelta(milliseconds=500)

    t1_a = t1.timestamp()
    t2_a = t2.timestamp()
    t3_a = t3.timestamp()
    t4_a = t4.timestamp()
    t5_a = t5.timestamp()
    t6_a = t6.timestamp()
    t7_a = t7.timestamp()
    t8_a = t8.timestamp()

    x1 = {"start": t1_a, "end": t2_a}
    x2_concludes = {"start": t3_a, "end": t4_a}
    x3_concludes = {"start": t5_a, "end": t6_a}
    x4 = {"start": t7_a, "end": t8_a}

    mock_mouse_facade.populate_event(x1)
    mock_mouse_facade.populate_event(x2_concludes)
    tracker.run_tracking_loop()
    mock_mouse_facade.populate_event(x3_concludes)
    tracker.run_tracking_loop()
    mock_mouse_facade.populate_event(x4)
    tracker.run_tracking_loop()
    # mock_mouse_facade.set_cursor_pos(x7)
    # tracker.run_tracking_loop()

    # Only check that the stops were logged, because they signal a closed window
    assert len(events) == len(
        [x2_concludes, x3_concludes]
    ), "Some mouse events were not recorded"


def test_multiple_handlers_are_called(tracker_and_events, mock_mouse_facade):
    """Test that when multiple handlers are provided, they are all called"""
    tracker = tracker_and_events[0]
    handler1_calls = []
    handler2_calls = []

    now = datetime.now() - timedelta(hours=1)
    t1 = now + timedelta(milliseconds=5)
    t2 = now + timedelta(milliseconds=35)
    t2i = now + timedelta(milliseconds=45)
    t2ii = now + timedelta(milliseconds=55)
    t3 = now + timedelta(milliseconds=1090)
    t4 = now + timedelta(milliseconds=1100)
    t5 = now + timedelta(milliseconds=2300)
    t6 = now + timedelta(milliseconds=2310)

    t1_a = t1.timestamp()
    t2_a = t2.timestamp()
    t2i_a = t2i.timestamp()
    t2ii_a = t2ii.timestamp()
    t3_a = t3.timestamp()
    t4_a = t4.timestamp()
    t5_a = t5.timestamp()
    t6_a = t6.timestamp()

    x1 = {"start": t1_a, "end": t2_a}
    x1i = {"start": t2i_a, "end": t2ii_a}
    x2 = {"start": t3_a, "end": t4_a}
    x3 = {"start": t5_a, "end": t6_a}

    def handler1(event):
        handler1_calls.append(event)

    def handler2(event):
        handler2_calls.append(event)

    # Replace single handler with multiple handlers
    tracker.event_handlers = [handler1, handler2]

    # Simulate mouse movement and stop
    mock_mouse_facade.populate_event(x1)
    mock_mouse_facade.populate_event(x1i)
    tracker.run_tracking_loop()
    mock_mouse_facade.populate_event(x2)
    tracker.run_tracking_loop()
    mock_mouse_facade.populate_event(x3)
    tracker.run_tracking_loop()

    num_of_gaps_greater_than_1000ms = 2

    assert len(handler1_calls) == len(handler2_calls) == num_of_gaps_greater_than_1000ms
    assert handler1_calls[0] == handler2_calls[0]


def test_threading_cleanup(mock_mouse_facade, event_collector):
    """Test that ThreadedMouseTracker cleans up properly on stop"""
    events, handler = event_collector
    tracker_core = MouseTrackerCore(mock_mouse_facade, handler)
    threaded_tracker = ThreadedTracker(tracker_core)

    threaded_tracker.start()

    assert threaded_tracker.is_running
    assert threaded_tracker.hook_thread is not None
    assert threaded_tracker.hook_thread.is_alive()

    threaded_tracker.stop()
    assert not threaded_tracker.is_running
    assert not threaded_tracker.hook_thread.is_alive()


# def test_end_program_routine_called(tracker_and_events, mock_mouse_facade):
#     """Test that end program routine is called when stopping tracker"""
#     end_program_called = []

#     now = datetime.now() - timedelta(hours=1)
#     t1 = now + timedelta(milliseconds=5)
#     t2 = now + timedelta(milliseconds=5)
#     t3 = now + timedelta(milliseconds=5)
#     t4 = now + timedelta(milliseconds=5)

#     t1_a = t1.timestamp()
#     t2_a = t2.timestamp()
#     t3_a = t3.timestamp()
#     t4_a = t4.timestamp()

#     x1 = {"start": t1_a, "end": t2_a}
#     x2 = {"start": t2_a, "end": t3_a}
#     x3 = {"start": t3_a, "end": t4_a}

#     def mock_end_program(report):
#         end_program_called.append(True)

#     tracker = tracker_and_events[0]
#     tracker.end_program_func = mock_end_program

#     # Simulate some movement
#     mock_mouse_facade.set_cursor_pos(x1)
#     tracker.run_tracking_loop()
#     mock_mouse_facade.set_cursor_pos(x2)
#     tracker.run_tracking_loop()
#     mock_mouse_facade.set_cursor_pos(x3)
#     tracker.run_tracking_loop()

#     tracker.stop()
#     assert len(end_program_called) == 1
