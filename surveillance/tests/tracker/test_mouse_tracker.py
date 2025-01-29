# t ests/test_mouse_tracker.py
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from datetime import datetime
import tempfile

# Import the module under test
# Assuming the original file is named mouse_tracker.py and is in a module called tracking
from src.util.detect_os import OperatingSystemInfo
from src.util.threaded_tracker import ThreadedTracker
from src.trackers.mouse_tracker import MouseTrackerCore, MouseEvent
from src.facade.mouse_facade import UbuntuMouseApiFacadeCore, MouseCoords

from ..mocks.mock_clock import MockClock


class MockMouseFacade():
    def __init__(self):
        self.cursor_pos = MouseCoords(0, 0)
        self.hook_thread = None

    def get_position_coords(self):
        return self.cursor_pos

    def set_cursor_pos(self, pos):
        self.cursor_pos = pos

    def get_position(self):
        return self.cursor_pos

    def stop(self):
        print("Stopping fake facade")


@pytest.fixture
def mock_clock():
    times = [
        datetime(2025, 1, 1, 12, 0, 0),
        datetime(2025, 1, 1, 12, 0, 1),
        datetime(2025, 1, 1, 12, 0, 2),
        datetime(2025, 1, 1, 12, 0, 3),
        datetime(2025, 1, 1, 12, 0, 4),
        datetime(2025, 1, 1, 12, 0, 5),
        datetime(2025, 1, 1, 12, 0, 6),
        datetime(2025, 1, 1, 12, 0, 7),
        datetime(2025, 1, 1, 12, 0, 8),
        datetime(2025, 1, 1, 12, 0, 9),
        datetime(2025, 1, 1, 12, 0, 10),
        datetime(2025, 1, 1, 12, 0, 11),
        datetime(2025, 1, 1, 12, 0, 12),
        datetime(2025, 1, 1, 12, 0, 13),
        datetime(2025, 1, 1, 12, 0, 14)
    ]
    return MockClock(times)


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
        events.append(event)

    return events, event_handler


@pytest.fixture
def tracker_and_events(mock_clock, mock_mouse_facade, event_collector):
    """Create a MouseTracker instance with mocked dependencies."""
    events, handler = event_collector
    os_environment = OperatingSystemInfo()
    if os_environment.is_ubuntu:
        with patch('Xlib.display') as mock_display, \
                patch('src.trackers.mouse_tracker.OperatingSystemInfo') as mock_os_info:
            mock_os_info.return_value.is_windows = False
            mock_os_info.return_value.is_ubuntu = True
            tracker = MouseTrackerCore(mock_clock, mock_mouse_facade, handler)
            yield tracker, events
            print("Stopping tracker")
            tracker.stop()
    if os_environment.is_windows:
        with patch('src.trackers.mouse_tracker.OperatingSystemInfo') as mock_os_info, \
                patch.dict('sys.modules', {'win32con': Mock(), 'ctypes': Mock()}):
            mock_os_info.return_value.is_windows = True
            mock_os_info.return_value.is_ubuntu = False
            mock_clock = MockClock()
            tracker = MouseTrackerCore(mock_clock, mock_mouse_facade, handler)
            yield tracker, events
            print("Stopping tracker")
            tracker.stop()


def test_tracker_initialization(tracker_and_events):
    """Test that the MouseTracker initializes correctly."""
    tracker = tracker_and_events[0]
    assert tracker.is_moving is False
    assert tracker.movement_start_time is None
    assert tracker.last_position is None

# TODO: make this test that event handlers actually handle


def test_make_sure_handler_actually_handles(tracker_and_events, mock_mouse_facade):
    x1 = MouseCoords(100, 100)
    x2 = MouseCoords(100, 200)  # move
    x3 = MouseCoords(100, 200)  # stop
    x4 = MouseCoords(200, 200)  # move
    x5 = MouseCoords(200, 200)  # stop
    x6 = MouseCoords(200, 250)  # move
    x7 = MouseCoords(200, 250)  # stop
    tracker = tracker_and_events[0]
    events = tracker_and_events[1]
    mock_mouse_facade.set_cursor_pos(x1)
    tracker.run_tracking_loop()
    mock_mouse_facade.set_cursor_pos(x2)
    tracker.run_tracking_loop()
    mock_mouse_facade.set_cursor_pos(x3)
    tracker.run_tracking_loop()
    mock_mouse_facade.set_cursor_pos(x4)
    tracker.run_tracking_loop()
    mock_mouse_facade.set_cursor_pos(x5)
    tracker.run_tracking_loop()
    mock_mouse_facade.set_cursor_pos(x6)
    tracker.run_tracking_loop()
    mock_mouse_facade.set_cursor_pos(x7)
    tracker.run_tracking_loop()

    # Only check that the stops were logged, because they signal a closed window
    assert len(events) == len(
        [x3, x5, x7]), "Some mouse events were not recorded"


def test_handle_mouse_move_start(tracker_and_events, mock_mouse_facade):
    """Test that _handle_mouse_move correctly handles movement start."""
    tracker, events = tracker_and_events

    # primed for retrieval  # Might be an object
    mock_mouse_facade.set_cursor_pos(MouseCoords(100, 200))

    tracker.run_tracking_loop()

    assert tracker.is_moving is False  # Because it's not
    assert tracker.last_position.x == 100 and tracker.last_position.y == 200
    assert tracker.movement_start_time is None  # Because it hasn't started yet
    assert len(events) == 0  # none completed


def test_handle_mouse_stop_moving(tracker_and_events, mock_mouse_facade):
    tracker, events = tracker_and_events

    # primed for retrieval  # Might be an object
    mock_mouse_facade.set_cursor_pos(MouseCoords(100, 200))

    tracker.run_tracking_loop()

    # primed for retrieval - moved 50 units
    mock_mouse_facade.set_cursor_pos(MouseCoords(100, 250))

    tracker.run_tracking_loop()

    assert tracker.is_moving
    assert tracker.last_position.x == 100 and tracker.last_position.y == 250
    assert tracker.movement_start_time is not None

    # primed for retrieval - moved nowhere
    mock_mouse_facade.set_cursor_pos(MouseCoords(100, 250))

    tracker.run_tracking_loop()

    assert tracker.is_moving is False
    assert tracker.last_position.x == 100 and tracker.last_position.y == 250
    assert tracker.movement_start_time is None
    assert len(events) == 1
    assert events[0].start_time is not None and events[0].end_time is not None


def test_handle_start_stop_start(tracker_and_events, mock_mouse_facade):
    tracker = tracker_and_events[0]

    # primed for retrieval  # Might be an object
    mock_mouse_facade.set_cursor_pos(MouseCoords(100, 200))

    tracker.run_tracking_loop()

    # primed for retrieval - moved 50 units
    mock_mouse_facade.set_cursor_pos(MouseCoords(100, 250))

    tracker.run_tracking_loop()

    assert tracker.is_moving
    assert tracker.last_position.x == 100 and tracker.last_position.y == 250
    assert tracker.movement_start_time is not None

    # primed for retrieval - moved nowhere
    mock_mouse_facade.set_cursor_pos(MouseCoords(100, 250))

    tracker.run_tracking_loop()

    assert tracker.is_moving is False
    assert tracker.last_position.x == 100 and tracker.last_position.y == 250
    assert tracker.movement_start_time is None

    mock_mouse_facade.set_cursor_pos(MouseCoords(200, 300))

    tracker.run_tracking_loop()

    assert tracker.is_moving
    assert tracker.last_position.x == 200 and tracker.last_position.y == 300
    assert tracker.movement_start_time is not None


def test_multiple_handlers_are_called(tracker_and_events, mock_mouse_facade):
    """Test that when multiple handlers are provided, they are all called"""
    tracker = tracker_and_events[0]
    handler1_calls = []
    handler2_calls = []

    def handler1(event):
        handler1_calls.append(event)

    def handler2(event):
        handler2_calls.append(event)

    # Replace single handler with multiple handlers
    tracker.event_handlers = [handler1, handler2]

    # Simulate mouse movement and stop
    mock_mouse_facade.set_cursor_pos(MouseCoords(100, 100))
    tracker.run_tracking_loop()
    mock_mouse_facade.set_cursor_pos(MouseCoords(150, 150))
    tracker.run_tracking_loop()
    mock_mouse_facade.set_cursor_pos(MouseCoords(150, 150))  # Stop
    tracker.run_tracking_loop()

    assert len(handler1_calls) == len(handler2_calls) == 1
    assert handler1_calls[0] == handler2_calls[0]


def test_diagonal_mouse_movement(tracker_and_events, mock_mouse_facade):
    """Test that diagonal mouse movements are tracked correctly"""
    tracker = tracker_and_events[0]
    events = tracker_and_events[1]

    # Simulate diagonal movement
    mock_mouse_facade.set_cursor_pos(MouseCoords(100, 100))
    tracker.run_tracking_loop()
    mock_mouse_facade.set_cursor_pos(MouseCoords(150, 150))
    tracker.run_tracking_loop()
    mock_mouse_facade.set_cursor_pos(MouseCoords(150, 150))  # Stop
    tracker.run_tracking_loop()

    assert len(events) == 1
    assert events[0].start_time is not None
    assert events[0].end_time is not None


def test_rapid_mouse_movement_windows(tracker_and_events, mock_mouse_facade):
    """Test tracking of rapid mouse movements with multiple position changes"""
    tracker = tracker_and_events[0]
    events = tracker_and_events[1]

    positions = [
        (100, 100),
        (120, 120),
        (140, 140),
        (160, 160),
        (160, 160)  # Stop
    ]

    for x, y in positions:
        mock_mouse_facade.set_cursor_pos(MouseCoords(x, y))
        tracker.run_tracking_loop()

    assert len(events) == 1
    assert events[0].start_time is not None
    assert events[0].end_time is not None


def test_mouse_position_with_negative_coordinates(tracker_and_events, mock_mouse_facade):
    """Test handling of negative mouse coordinates"""
    tracker = tracker_and_events[0]
    events = tracker_and_events[1]

    # Simulate movement with negative coordinates
    mock_mouse_facade.set_cursor_pos(MouseCoords(-100, -100))
    tracker.run_tracking_loop()
    mock_mouse_facade.set_cursor_pos(MouseCoords(-150, -150))
    tracker.run_tracking_loop()
    mock_mouse_facade.set_cursor_pos(MouseCoords(-150, -150))  # Stop
    tracker.run_tracking_loop()

    assert len(events) == 1
    assert events[0].start_time is not None
    assert events[0].end_time is not None


def test_zero_distance_movement(tracker_and_events, mock_mouse_facade):
    """Test that zero-distance movements are handled correctly"""
    tracker = tracker_and_events[0]
    events = tracker_and_events[1]

    # Simulate movement to same position
    mock_mouse_facade.set_cursor_pos(MouseCoords(100, 100))
    tracker.run_tracking_loop()
    # Testing starting circumstances
    assert tracker.is_moving is False, "Should be false"
    assert tracker.last_position.x == 100 and tracker.last_position.y == 100
    assert tracker.movement_start_time is None

    mock_mouse_facade.set_cursor_pos(MouseCoords(100, 100))
    tracker.run_tracking_loop()  # FIXME
    # Testing starting circumstances
    assert tracker.is_moving is False, "Should still be false"
    assert tracker.last_position.x == 100 and tracker.last_position.y == 100
    assert tracker.movement_start_time is None

    # Assert
    # No movement window should be created
    assert len(events) == 0, "A movement window was created when it shouldn't be"


def test_threading_cleanup(mock_clock, mock_mouse_facade, event_collector):
    """Test that ThreadedMouseTracker cleans up properly on stop"""
    events, handler = event_collector
    tracker_core = MouseTrackerCore(mock_clock, mock_mouse_facade, handler)
    threaded_tracker = ThreadedTracker(tracker_core)

    threaded_tracker.start()
    assert threaded_tracker.is_running
    assert threaded_tracker.hook_thread.is_alive()
    assert threaded_tracker.hook_thread is not None

    threaded_tracker.stop()
    assert not threaded_tracker.is_running
    assert not threaded_tracker.hook_thread.is_alive()


def test_end_program_routine_called(tracker_and_events, mock_mouse_facade):
    """Test that end program routine is called when stopping tracker"""
    end_program_called = []

    def mock_end_program(report):
        end_program_called.append(True)

    tracker = tracker_and_events[0]
    tracker.end_program_func = mock_end_program

    # Simulate some movement
    mock_mouse_facade.set_cursor_pos(MouseCoords(100, 100))
    tracker.run_tracking_loop()
    mock_mouse_facade.set_cursor_pos(MouseCoords(150, 150))
    tracker.run_tracking_loop()
    mock_mouse_facade.set_cursor_pos(MouseCoords(150, 150))
    tracker.run_tracking_loop()

    tracker.stop()
    assert len(end_program_called) == 1

# def test_preserve_open_events(tracker):
#     """Test that preserve_open_events correctly handles open movement sessions."""
#     events = [
#         {'event_type': MouseEvent.START, 'x_position': 100, 'y_position': 200},
#         {'event_type': MouseEvent.STOP, 'x_position': 150, 'y_position': 250},
#         {'event_type': MouseEvent.START, 'x_position': 150, 'y_position': 250},
#         {'event_type': MouseEvent.STOP, 'x_position': 210, 'y_position': 250},
#         {'event_type': MouseEvent.START, 'x_position': 210, 'y_position': 290}
#     ]

#     preserved = tracker.preserve_open_events(events)
#     assert len(preserved) == 1
#     assert preserved[0]['event_type'] == MouseEvent.START
