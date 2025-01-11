import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
import tempfile
import csv
from surveillance.src.surveillance_manager import ProductivityTracker

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def tracker(temp_dir):
    tracker = ProductivityTracker()
    tracker.data_dir = Path(temp_dir)
    return tracker

@pytest.fixture
def sample_window_info():
    return {
        'title': 'test.py - Visual Studio Code',
        'process_name': 'code.exe',
        'pid': 1234,
        'timestamp': datetime.now()
    }

def test_init(tracker):
    """Test initialization of ProductivityTracker"""
    assert isinstance(tracker.productive_apps, dict)
    assert isinstance(tracker.productive_categories, dict)
    assert isinstance(tracker.productive_sites, list)
    assert tracker.current_window is None
    assert tracker.start_time is None
    assert isinstance(tracker.session_data, list)

@pytest.mark.parametrize("window_info,expected", [
    ({
        'process_name': 'code.exe',
        'title': 'test.py - VSCode',
        'pid': 1234,
        'timestamp': datetime.now()
    }, True),
    ({
        'process_name': 'chrome.exe',
        'title': 'Stack Overflow - Google Chrome',
        'pid': 1234,
        'timestamp': datetime.now()
    }, True),
    ({
        'process_name': 'chrome.exe',
        'title': 'Facebook - Google Chrome',
        'pid': 1234,
        'timestamp': datetime.now()
    }, False),
    ({
        'process_name': 'discord.exe',
        'title': 'team-backend - Discord',
        'pid': 1234,
        'timestamp': datetime.now()
    }, True),
])
def test_is_productive(tracker, window_info, expected):
    """Test productivity classification for different windows"""
    print(window_info, "66rm")
    assert tracker.is_productive(window_info) == expected

def test_track_window_new_session(tracker):
    """Test tracking a new window session"""
    with patch.object(tracker, 'get_active_window_info') as mock_get_info:
        mock_get_info.return_value = {
            'title': 'test.py - VSCode',
            'process_name': 'code.exe',
            'pid': 1234,
            'timestamp': datetime.now()
        }
        
        tracker.track_window()
        assert tracker.current_window == 'code.exe - test.py - VSCode'
        assert tracker.start_time is not None

def test_track_window_change(tracker):
    """Test handling window changes"""
    with patch.object(tracker, 'get_active_window_info') as mock_get_info:
        # First window
        mock_get_info.return_value = {
            'title': 'test.py - VSCode',
            'process_name': 'code.exe',
            'pid': 1234,
            'timestamp': datetime.now()
        }
        tracker.track_window()
        
        # Change window
        mock_get_info.return_value = {
            'title': 'Stack Overflow - Google Chrome',
            'process_name': 'chrome.exe',
            'pid': 5678,
            'timestamp': datetime.now()
        }
        with patch.object(tracker, 'log_session') as mock_log:
            tracker.track_window()
            mock_log.assert_called_once()

def test_log_session(tracker):
    """Test session logging"""
    tracker.current_window = 'code.exe - test.py - VSCode'
    tracker.start_time = datetime.now() - timedelta(minutes=30)
    
    with patch.object(tracker, 'save_session') as mock_save:
        tracker.log_session()
        mock_save.assert_called_once()
        session_data = mock_save.call_args[0][0]
        
        assert 'start_time' in session_data
        assert 'end_time' in session_data
        assert 'duration' in session_data
        assert 'window' in session_data
        assert 'productive' in session_data

def test_save_session(tracker):
    """Test saving session data to CSV"""
    session = {
        'start_time': datetime.now().isoformat(),
        'end_time': (datetime.now() + timedelta(minutes=30)).isoformat(),
        'duration': 1800,
        'window': 'code.exe - test.py - VSCode',
        'productive': True
    }
    
    tracker.save_session(session)
    
    # Check if file was created and contains correct data
    csv_file = list(tracker.data_dir.glob('productivity_*.csv'))[0]
    assert csv_file.exists()
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        saved_session = next(reader)
        assert saved_session['window'] == session['window']
        assert float(saved_session['duration']) == session['duration']
        assert saved_session['productive'].lower() == str(session['productive']).lower()

def test_generate_report(tracker):
    """Test report generation"""
    # Create test data
    sessions = [
        {
            'start_time': datetime.now().isoformat(),
            'end_time': (datetime.now() + timedelta(hours=2)).isoformat(),
            'duration': 7200,  # 2 hours
            'window': 'code.exe - test.py - VSCode',
            'productive': True
        },
        {
            'start_time': datetime.now().isoformat(),
            'end_time': (datetime.now() + timedelta(hours=1)).isoformat(),
            'duration': 3600,  # 1 hour
            'window': 'chrome.exe - GitHub - Google Chrome',
            'productive': True
        }
    ]

    for session in sessions:
        tracker.save_session(session)
    
    report = tracker.generate_report()
    
    assert isinstance(report, dict)
    assert report['productive_time'] == 3.0  # 3 hours total
    assert 'app_times' in report
    assert report['app_times']['VSCode'] == 2.0
    assert isinstance(report['app_times']['Chrome'], dict)  # Chrome should have nested site data

if __name__ == '__main__':
    pytest.main([__file__])