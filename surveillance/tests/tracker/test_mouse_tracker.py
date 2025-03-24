# t ests/test_mouse_tracker.py
from annotated_types import T
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from datetime import datetime, timedelta
import tempfile

from src.util.detect_os import OperatingSystemInfo
from src.util.threaded_tracker import ThreadedTracker
from src.trackers.mouse_tracker import MouseTrackerCore, MouseEvent
# from src.facade.mouse_facade import MouseCoords


class MockMouseFacade():
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


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmp_path = Path(tmpdirname)
        yield tmp_path
        # Cleanup: remove any CSV files
        for csv_file in tmp_path.glob('*.csv'):
            csv_file.unlink()


@pytest.fixture
def mock_mouse_facade():
    """Create a mock mouse API facade."""
    return MockMouseFacade()


@pytest.fixture
def event_collector():
    """Creates a collector and handler for mouse events"""
    events = []

    def event_handler(event):
        print(event, "in event handler 68ru")
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

    # Spy on the session window has elapsed function
    session_window_has_elapsed_spy = Mock(
        side_effect=tracker.aggregator.session_window_has_elapsed)
    tracker.aggregator.session_window_has_elapsed = session_window_has_elapsed_spy

    a1 = datetime.now().replace(microsecond=0) - timedelta(hours=1)
    a2 = a1 + timedelta(milliseconds=5)
    a3 = a2 + timedelta(milliseconds=16)

    b1 = a3 + timedelta(milliseconds=1127)
    b2 = b1 + timedelta(milliseconds=25)
    b3 = b2 + timedelta(milliseconds=22)

    c1 = b3 + timedelta(milliseconds=4105)
    c2 = c1 + timedelta(milliseconds=33)
    c3 = c2 + timedelta(milliseconds=21)
    c4 = c3 + timedelta(milliseconds=4)

    a1 = a1.timestamp()
    a2 = a2.timestamp()
    a3 = a3.timestamp()

    b1 = b1.timestamp()
    b2 = b2.timestamp()
    b3 = b3.timestamp()

    c1 = c1.timestamp()
    c2 = c2.timestamp()
    c3 = c3.timestamp()
    c4 = c4.timestamp()

    ax1 = {"start": a1, "end": a2}
    ax2 = {"start": a2, "end": a3}

    bx1 = {"start": b1, "end": b2}
    bx2 = {"start": b2, "end": b3}

    cx1 = {"start": c1, "end": c2}
    cx2 = {"start": c2, "end": c3}
    cx3 = {"start": c3, "end": c4}

    # Spy on add_event
    add_event_spy = Mock(side_effect=tracker.aggregator.add_event)
    tracker.aggregator.add_event = add_event_spy

    assert tracker.aggregator.current_aggregation is None, "Faulty setup conditions"

    mock_mouse_facade.set_cursor_pos(ax1)
    mock_mouse_facade.set_cursor_pos(ax2)
    tracker.run_tracking_loop()
    # Both the start and end times were added to aggregator
    assert len(tracker.aggregator.current_aggregation.events) == 4
    assert add_event_spy.call_count == 4, "Start and end times were supposed to be added"

    assert tracker.aggregator.current_aggregation.start_time == ax1["start"]
    # 2nd event closes window
    assert tracker.aggregator.current_aggregation.end_time == ax2["end"]

    mock_mouse_facade.set_cursor_pos(bx1)
    mock_mouse_facade.set_cursor_pos(bx2)
    tracker.run_tracking_loop()
    assert len(events) == 1  # ax1, ax2
    # A new array

    assert len(tracker.aggregator.current_aggregation.events) == 3
    assert tracker.aggregator.current_aggregation.start_time == bx1["start"]
    assert tracker.aggregator.current_aggregation.end_time == bx2["end"]
    # Note: 4 + 3 = 7, so 3 new calls from this group
    assert add_event_spy.call_count == 7, "Start & end times were not added"

    # Three in a row
    mock_mouse_facade.set_cursor_pos(cx1)
    mock_mouse_facade.set_cursor_pos(cx2)
    mock_mouse_facade.set_cursor_pos(cx3)
    tracker.run_tracking_loop()
    assert tracker.aggregator.current_aggregation.end_time == cx3["end"]
    assert len(tracker.aggregator.current_aggregation.events) == 5
    # Note: 7 + 5 = 12, so 5 new calls from this group.
    assert add_event_spy.call_count == 12  # (start, end) * 2

    # Only check that the stops were logged, because they signal a closed window
    ##
    # NOTE: This assertion here is the real point of the test!
    ##
    handler_calls_count = 2
    assert len(
        events) == handler_calls_count, "Some mouse events were not recorded"


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
