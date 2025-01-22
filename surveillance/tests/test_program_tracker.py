import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

from .mocks.mock_clock import MockClock

from src.config.definitions import productive_apps, productive_sites
from src.object.classes import ProgramSessionData
from src.trackers.program_tracker import ProgramTrackerCore
from src.util.strings import no_space_dash_space


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

ex3 = {'os': 'Ubuntu', 'pid': 128216, 'process_name': 'Xorg',
       'window_title': 'H&M | Online Fashion, Homeware & Kids Clothes | H&M CA - Google Chrome'}
ex4 = {'os': 'Ubuntu', 'pid': 128216,
       'process_name': 'Xorg', 'window_title': 'Alt-tab window'}
ex5 = {'os': 'Ubuntu', 'pid': 128216, 'process_name': 'Xorg',
       'window_title': 'program_tracker.py - deskSense - Visual Studio Code'}


def test_is_productive_chrome_productive():
    """Test that Chrome is marked productive when on productive sites"""
    clock = MockClock([datetime.now()])
    facade = Mock()
    tracker = ProgramTrackerCore(clock, facade, Mock())

    window_info_1 = {
        'process_name': 'Google Chrome',
        'window_title': 'stackoverflow.com - Google Chrome'
    }
    # productive_window_2 = {'os': 'Ubuntu', 'pid': 128216, 'process_name': 'Xorg',
    #                        'window_title': 'program_tracker.py - deskSense - Visual Studio Code'}
    productive_window_3 = {'os': 'Ubuntu', 'pid': 129614, 'process_name': 'chrome',
                           'window_title': 'Squashing Commits with Git Rebase - Claude - Google Chrome'}

    assert tracker.is_productive(
        window_info_1, productive_apps, productive_sites) == True
    assert tracker.is_productive(
        productive_window_3, productive_apps, productive_sites) == True


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

    assert tracker.is_productive(
        window_info, productive_apps, productive_sites) == False
    assert tracker.is_productive(
        window_info_2, productive_apps, productive_sites) == False


def test_start_new_session():
    t1_start = datetime(2024, 1, 1, 12, 2)

    start_time = t1_start
    times = [start_time, ]
    clock = MockClock(times)
    clock.now = MagicMock(wraps=clock.now)
    facade = Mock()
    handler = Mock()

    tracker = ProgramTrackerCore(clock, facade, handler)

    assert tracker.current_session is None

    # Act
    window_change = {'os': 'Ubuntu', 'pid': 128216, 'process_name': 'Xorg',
                     'window_title': 'program_tracker.py - deskSense - Visual Studio Code'}
    current_time = tracker.clock.now()
    new_session = tracker.start_new_session(
        window_change, current_time)

    # Assert
    clock.now.assert_called_once()
    assert new_session.window_title is not None
    assert new_session.detail is not None
    assert new_session.start_time is not None

    assert new_session.end_time is None
    assert new_session.duration is None

    assert new_session.window_title == "Visual Studio Code"
    assert new_session.detail == "program_tracker.py - deskSense"
    assert new_session.start_time is current_time


def test_conclude_session():
    t1_start = datetime(2024, 1, 1, 12, 2)
    t2_end = datetime(2024, 1, 1, 12, 4)
    t3_start = datetime(2024, 1, 1, 12, 7)
    t4_end = datetime(2024, 1, 1, 12, 10)

    start_time = t1_start
    times = [start_time]
    clock = MockClock(times)
    # clock.now = MagicMock(wraps=clock.now)
    facade = Mock()
    handler = Mock()

    tracker = ProgramTrackerCore(clock, facade, handler)

    assert tracker.current_session is None

    window_change = {'os': 'Ubuntu', 'pid': 128216, 'process_name': 'Xorg',
                     'window_title': 'program_tracker.py - deskSense - Visual Studio Code'}

    started_session = tracker.start_new_session(
        window_change, t1_start)

    tracker.current_session = started_session

    # Act
    tracker.conclude_session(t2_end)

    retrieved_session = tracker.current_session

    # Assert
    assert retrieved_session.end_time is not None
    assert retrieved_session.duration is not None

    assert retrieved_session.start_time == t1_start  # called start_time
    assert retrieved_session.end_time == t2_end
    assert retrieved_session.duration == (t2_end - t1_start)


def test_window_change_triggers_handler():
    """Test that window changes trigger event handlers"""
    time_from_previous_program = datetime(2024, 1, 1, 12, 0)
    t1_start = datetime(2024, 1, 1, 12, 2)
    t2_end = datetime(2024, 1, 1, 12, 4)
    t3_start = datetime(2024, 1, 1, 12, 7)
    t4_end = datetime(2024, 1, 1, 12, 10)

    start_time = t1_start
    times = [start_time, t2_end, t3_start, t4_end]
    clock = MockClock(times)
    clock.now = MagicMock(wraps=clock.now)
    facade = Mock()
    handler = Mock()

    tracker = ProgramTrackerCore(clock, facade, handler)

    # Set up facade to yield a window change
    first_test_item = {
        'process_name': 'code',
        'window_title': 'test.py - Visual Studio Code',
        "os": "Ubuntu"
    }
    facade.listen_for_window_changes.return_value = iter([first_test_item])
    # facade.listen_for_window_changes.side_effect = lambda: (print("FOO BAR") or iter([{
    #     'process_name': 'code',
    #     'window_title': 'test.py - Visual Studio Code',
    #     "os": "Ubuntu"
    # }]))

    tracker.clock.now.assert_not_called()
    assert tracker.current_session is None  # Test setup conditions

    # ### Act - Run the tracker
    tracker.run_tracking_loop()
    tracker.clock.now.assert_called()
    # There was no session from a prev run so, on_a_different_window is false
    assert tracker.current_session.window_title == "Visual Studio Code"
    assert tracker.current_session.end_time is None
    handler.assert_not_called()

    # # Continue acting - Need to run the tracking loop again to close a session

    facade.listen_for_window_changes.return_value = [ex3]
    tracker.run_tracking_loop()
    assert tracker.clock.now.call_count == 2

    # Verify handler was called with session data
    handler.assert_called_once()

    session_arg = handler.call_args[0][0]
    assert isinstance(session_arg, ProgramSessionData)
    assert hasattr(session_arg, 'window_title')
    assert hasattr(session_arg, 'productive')
    assert hasattr(session_arg, 'duration')

    deliverable = session_arg

    assert deliverable.start_time != deliverable.end_time

    assert deliverable.window_title == "Visual Studio Code"
    assert deliverable.detail == "test.py"
    assert deliverable.start_time == t1_start
    assert deliverable.end_time == t2_end
    assert deliverable.duration == (t2_end - t1_start)


def test_handle_alt_tab_window():
    """Test handling of 'Alt-tab window' title"""
    clock = MockClock([datetime.now()])
    facade = Mock()
    tracker = ProgramTrackerCore(clock, facade, Mock())

    example = {'os': 'Ubuntu', 'pid': 128216,
               'process_name': 'Xorg', 'window_title': 'Alt-tab window'}

    time = clock.now()

    session = tracker.start_new_session(
        window_change_dict=example, start_time=time)

    assert session.window_title == 'Alt-tab window'


def test_a_series_of_programs():
    """ 
    A very long test. 
    This test shows that the run_tracking_loop() works as expected when given, a series of changes.
    """

    t1 = datetime(2024, 1, 1, 12, 2)
    t2 = datetime(2024, 1, 1, 12, 4)
    t3 = datetime(2024, 1, 1, 12, 7)
    t4 = datetime(2024, 1, 1, 12, 10)
    t5 = datetime(2024, 1, 1, 12, 14)
    t6 = datetime(2024, 1, 1, 12, 15)
    t7 = datetime(2024, 1, 1, 12, 19)

    clock = MockClock([t1, t2, t3, t4, t5, t6, t7])
    clock = MagicMock(wraps=clock)
    facade = Mock()
    handler = Mock()
    tracker = ProgramTrackerCore(clock, facade, handler)

    handler1_calls = []
    handler2_calls = []

    def handler1(event):
        handler1_calls.append(event)

    def handler2(event):
        handler2_calls.append(event)

    # Replace single handler with multiple handlers
    tracker.event_handlers = [handler1, handler2]

    # Setup
    program1 = {"os": "some_val", 'process_name': 'code',
                'window_title': 'Alt-tab window'}
    facade.listen_for_window_changes.return_value = iter([program1])

    # Act
    tracker.run_tracking_loop()  # 1

    # ### Assert
    # Session is open, not concluded
    assert tracker.current_session is not None
    assert tracker.current_session.start_time
    assert tracker.current_session.window_title == program1["window_title"]
    assert tracker.current_session.detail == no_space_dash_space
    assert tracker.current_session.end_time is None
    assert len(handler1_calls) == 0 and len(handler2_calls) == 0

    # More setup
    program2 = {"os": "some_val", 'process_name': 'Xorg',
                'window_title': 'rlm@kingdom: ~/Code/deskSense/surveillance'}
    facade.listen_for_window_changes.return_value = iter([program2])
    # Act
    tracker.run_tracking_loop()  # 2

    # ### Assert
    assert tracker.current_session.window_title == program2['window_title']
    assert tracker.current_session.detail == no_space_dash_space
    assert tracker.current_session.start_time is not None
    assert tracker.current_session.end_time is None
    assert clock.now.call_count == 2
    assert len(handler1_calls) == 1
    assert len(handler2_calls) == 1

    # More setup
    program3 = {"os": "some_val", 'process_name': 'Xorg',
                'window_title': 'Vite + React + TS - Google Chrome'}
    facade.listen_for_window_changes.return_value = iter([program3])
    # Act
    tracker.run_tracking_loop()

    # Assert
    assert tracker.current_session.window_title == "Google Chrome"
    assert tracker.current_session.detail == "Vite + React + TS"
    assert clock.now.call_count == 3
    assert len(handler1_calls) == 2

    # More setup
    program4 = {"os": "some_val", 'process_name': None,
                'window_title': 'Alt-tab window'}

    facade.listen_for_window_changes.return_value = iter([program4])
    # Act
    tracker.run_tracking_loop()

    # Assert
    assert tracker.current_session.window_title == program4["window_title"]
    assert clock.now.call_count == 4
    assert len(handler1_calls) == 3

    # More setup
    program5 = {"os": "some_val", 'process_name': 'Xorg',
                'window_title': 'program_tracker.py - deskSense - Visual Studio Code'}
    facade.listen_for_window_changes.return_value = iter([program5])
    # Act
    tracker.run_tracking_loop()

    # Assert
    assert tracker.current_session.window_title == "Visual Studio Code"
    assert clock.now.call_count == 5

    # ### Final assertions
    assert len(handler1_calls) == 4  # Not five: The fifth remains open
    assert len(handler2_calls) == 4  # Not five: The fifth remains open
    assert tracker.current_session.end_time is None  # See?
    assert tracker.current_session.detail == "program_tracker.py - deskSense"
