# def test_log_movement():
#     pass
#     # todo: stub csv.DictWriter

# def test_generate_movement_report():
#     pass
#     # todo: need a csv with content

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from datetime import datetime
import csv
import tempfile
from enum import Enum, auto

# Import the module under test
# Assuming the original file is named mouse_tracker.py and is in a module called tracking
from src.trackers.mouse_tracker import MouseTracker, MouseEvent, MouseApiFacade

class MockMouseFacade(MouseApiFacade):
    def __init__(self):
        self.cursor_pos = (0, 0)
    
    def get_cursor_pos(self):
        return self.cursor_pos
    
    def set_cursor_pos(self, pos):
        self.cursor_pos = pos

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
def tracker(temp_data_dir, mock_mouse_facade):
    """Create a MouseTracker instance with mocked dependencies."""
    print("49rm")
    with patch('src.trackers.mouse_tracker.OperatingSystemInfo') as mock_os_info, \
         patch.dict('sys.modules', {'win32con': Mock(), 'ctypes': Mock()}):
        mock_os_info.return_value.is_windows = True
        mock_os_info.return_value.is_ubuntu = False
        print("53rm")
        tracker = MouseTracker(temp_data_dir, mock_mouse_facade)
        yield tracker
        tracker.stop()

def test_tracker_initialization(tracker, temp_data_dir):
    """Test that the MouseTracker initializes correctly."""
    assert tracker.data_dir == temp_data_dir
    assert not tracker.is_moving
    assert tracker.movement_start is None
    assert tracker.last_position is None

def test_log_movement_creates_csv(tracker, temp_data_dir):
    """Test that _log_movement creates a CSV file with correct headers."""
    print("66rm")
    position = (100, 200)
    date_str = datetime.now().strftime('%Y-%m-%d')
    expected_file = temp_data_dir / f'mouse_tracking_{date_str}.csv'
    
    tracker._log_movement_to_csv(MouseEvent.START, position)
    
    assert expected_file.exists()
    
    with open(expected_file, 'r') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        assert headers == ['timestamp', 'event_type', 'x_position', 'y_position']

def test_handle_mouse_move_start(tracker, mock_mouse_facade):
    """Test that _handle_mouse_move correctly handles movement start."""
    mock_mouse_facade.set_cursor_pos((100, 200))
    
    tracker._handle_mouse_move()
    
    assert tracker.is_moving
    assert tracker.last_position == (100, 200)
    assert tracker.movement_start is not None

def test_gather_session_empty(tracker):
    """Test that gather_session returns empty list when no movements recorded."""
    assert tracker.gather_session() == []

# # read to here - rm jan 13

def test_gather_session_with_data(tracker):
    """Test that gather_session returns recorded movements."""
    # Simulate some mouse movements
    position1 = (100, 200)
    position2 = (105, 250)
    tracker._log_movement_to_csv(MouseEvent.START, position1)
    tracker._log_movement_to_csv(MouseEvent.STOP, position2)
    
    session_data = tracker.gather_session()
    assert len(session_data) == 2
    assert session_data[0]['event_type'] == MouseEvent.START
    assert session_data[1]['event_type'] == MouseEvent.STOP

def test_preserve_open_events(tracker):
    """Test that preserve_open_events correctly handles open movement sessions."""
    events = [
        {'event_type': MouseEvent.START, 'x_position': 100, 'y_position': 200},
        {'event_type': MouseEvent.STOP, 'x_position': 150, 'y_position': 250},
        {'event_type': MouseEvent.START, 'x_position': 150, 'y_position': 250}
    ]
    
    preserved = tracker.preserve_open_events(events)
    assert len(preserved) == 1
    assert preserved[0]['event_type'] == MouseEvent.START

def test_generate_movement_report_empty(tracker, temp_data_dir):
    """Test generate_movement_report with no data."""
    date_str = datetime.now().strftime('%Y-%m-%d')
    report = tracker.generate_movement_report(date_str)
    
    assert isinstance(report, str)
    assert "No mouse tracking data available" in report