import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from .mocks.mock_clock import MockClock

from src.trackers.program_tracker import ProgramTrackerCore


@pytest.fixture
def mock_facade():
    facade = Mock()
    facade.read_current_program_info.return_value = {
        'os': 'Ubuntu',
        'pid': 12345,
        'process_name': 'chrome',
        'window_title': 'Test Window - Google Chrome'
    }
    return facade


@pytest.fixture
def mock_event_handler():
    return Mock()


@pytest.fixture
def times():
    return [
        datetime(2024, 1, 1, 12, 0),
        datetime(2024, 1, 1, 12, 1)
    ]


@pytest.fixture
def clock(times):
    return MockClock(times)


@pytest.fixture
def tracker(mock_facade, mock_event_handler, clock):
    return ProgramTrackerCore(clock, mock_facade, mock_event_handler)


# TODO: Test "for window_change in self.program_facade.listen_for_window_changes()" returns dict containing such and such
# TODO: Or *assume* that it does in a test somewhere.


def test_is_productive_chrome_productive():
    """Test that Chrome is marked productive when on productive sites"""
    clock = MockClock([datetime.now()])
    facade = Mock()
    tracker = ProgramTrackerCore(clock, facade, Mock())

    window_info_1 = {
        'process_name': 'Google Chrome',
        'window_title': 'stackoverflow.com - Google Chrome'
    }
    productive_window_2 = {'os': 'Ubuntu', 'pid': 128216, 'process_name': 'Xorg',
                           'window_title': 'program_tracker.py - deskSense - Visual Studio Code'}
    productive_window_3 = {'os': 'Ubuntu', 'pid': 129614, 'process_name': 'chrome',
                           'window_title': 'Squashing Commits with Git Rebase - Claude - Google Chrome'}

    print(productive_window_2, '120ru')
    assert tracker.is_productive(window_info_1) == True
    assert tracker.is_productive(productive_window_2) == True
    assert tracker.is_productive(productive_window_3) == True


def test_is_productive_chrome_unproductive():
    """Test that Chrome is marked unproductive on other sites"""
    clock = MockClock([datetime.now()])
    facade = Mock()
    tracker = ProgramTrackerCore(clock, facade, Mock())

    window_info = {
        'process_name': 'Google Chrome',
        'window_title': 'YouTube - Google Chrome'
    }
    window_info_2 = {
        'process_name': 'Google Chrome',
        'window_title': 'Tiktok - Google Chrome'
    }

    assert tracker.is_productive(window_info) == False
    assert tracker.is_productive(window_info_2) == False


# def test_package_window_into_db_entry():
#     """Test that window sessions are packaged correctly"""
#     start_time = datetime(2024, 1, 1, 12, 0)
#     end_time = datetime(2024, 1, 1, 12, 1)
#     times = [start_time, end_time]
#     clock = MockClock(times)

#     facade = Mock()
#     tracker = ProgramTrackerCore(clock, facade, Mock())

#     tracker.current_window = "Visual Studio Code - test.py"
#     tracker.start_time = start_time

#     window_info = {
#         'process_name': 'code',
#         'window_title': 'test.py - Visual Studio Code'
#     }

#     session = tracker.package_for_db_entry(window_info)

#     assert session['window'] == 'test.py'
#     assert session['start_time'] == start_time
#     assert session['end_time'] == end_time
#     assert session['duration'] == 60  # 1 minute in seconds
#     assert session['productive'] == True


def test_window_change_triggers_handler():
    """Test that window changes trigger event handlers"""
    time_from_previous_program = datetime(2024, 1, 1, 12, 0)
    start_time = datetime(2024, 1, 1, 12, 2)
    times = [start_time, datetime(2024, 1, 1, 12, 4)]
    clock = MockClock(times)
    facade = Mock()
    handler = Mock()

    tracker = ProgramTrackerCore(clock, facade, handler)

    # Set up facade to yield a window change
    # facade.listen_for_window_changes.return_value = iter([{
    #     'process_name': 'code',
    #     'window_title': 'test.py - Visual Studio Code',
    #     "os": "Ubuntu"
    # }])
    facade.listen_for_window_changes.side_effect = lambda: (print("FOO BAR") or iter([{
        'process_name': 'code',
        'window_title': 'test.py - Visual Studio Code',
        "os": "Ubuntu"
    }]))

    tracker.current_window = True  # Cooking the test environment
    tracker.start_time = time_from_previous_program

    # Act - Run the tracker
    tracker.run_tracking_loop()

    # Verify handler was called with session data
    handler.assert_called_once()
    session_arg = handler.call_args[0][0]
    assert isinstance(session_arg, dict)
    assert 'window' in session_arg
    assert 'productive' in session_arg


# def test_handle_alt_tab_window():
#     """Test handling of 'Alt-tab window' title"""
#     clock = MockClock([datetime.now()])
#     facade = Mock()
#     tracker = ProgramTrackerCore(clock, facade, Mock())

#     window_info = {
#         'process_name': 'Xorg',
#         'window_title': 'Alt-tab window'
#     }

#     session = tracker.package_for_db_entry(window_info)
#     assert session['window'] == 'Alt-tab window'

def test_a_series_of_programs():
    order = [
        {'process_name': 'code', 'window_title': 'Alt-tab window'},
        {'process_name': 'Xorg',
            'window_title': 'rlm@kingdom: ~/Code/deskSense/surveillance'},
        {'process_name': 'Xorg', 'window_title': 'Vite + React + TS - Google Chrome'},
        {'process_name': None, 'window_title': 'Alt-tab window'},
        {'process_name': 'chrome',
            'window_title': 'rlm@kingdom: ~/Code/deskSense/surveillance'},
        {'process_name': 'Xorg',
            'window_title': 'program_tracker.py - deskSense - Visual Studio Code'},
        {'process_name': 'Xorg', 'window_title': 'Alt-tab window'},
        {'process_name': None, 'window_title': 'rlm@kingdom: ~/Code/deskSense/surveillance'}
    ]
    # this test shows that the run_tracking_loop() works as expected when given, a series of changes.
