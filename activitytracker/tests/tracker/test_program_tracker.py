import pytest
from unittest.mock import MagicMock, Mock

from datetime import datetime, timedelta, timezone

from activitytracker.config.definitions import (
    no_space_dash_space,
    productive_apps,
    productive_sites,
)
from activitytracker.object.classes import CompletedProgramSession, ProgramSession
from activitytracker.trackers.program_tracker import ProgramTrackerCore
from activitytracker.util.time_wrappers import UserLocalTime

from ..mocks.mock_clock import MockClock


@pytest.fixture
def mock_facade():
    facade = Mock()
    facade.read_current_program_info.return_value = {
        "os": "Ubuntu",
        "pid": 12345,
        "process_name": "chrome",
        "window_title": "Test Window - Google Chrome",
    }
    return facade


@pytest.fixture
def mock_event_handler():
    return Mock()


@pytest.fixture
def times():
    return [datetime(2024, 1, 1, 12, 0), datetime(2024, 1, 1, 12, 1)]


@pytest.fixture
def clock(times):
    return MockClock(times)


@pytest.fixture
def tracker(mock_facade, mock_event_handler, clock):

    return ProgramTrackerCore(clock, mock_facade, mock_event_handler)


ex3 = {
    "os": "Ubuntu",
    "pid": 128216,
    "process_name": "Xorg",
    "exe_path": "C:/some/imaginary/path.exe",
    "window_title": "H&M | Online Fashion, Homeware & Kids Clothes | H&M CA - Google Chrome",
}
ex4 = {
    "os": "Ubuntu",
    "pid": 128216,
    "process_name": "Xorg",
    "exe_path": "C:/some/imaginary/other/path2.exe",
    "window_title": "Alt-tab window",
}
ex5 = {
    "os": "Ubuntu",
    "pid": 128216,
    "process_name": "Xorg",
    "exe_path": "C:/some/imaginary/path/again.exe",
    "window_title": "program_tracker.py - deskSense - Visual Studio Code",
}


def test_start_new_session():
    t1_start = datetime(2024, 1, 1, 12, 2)

    start_time = t1_start
    times = [
        start_time,
    ]
    clock = MockClock(times)
    clock.now = MagicMock(wraps=clock.now)
    facade = Mock()
    handler = Mock()

    tracker = ProgramTrackerCore(clock, facade, handler)

    assert tracker.current_session is None, "Initialization condition wasn't met"

    # assert tracker.current_session.window_title == "", "Initialization conditions weren't met"
    # assert tracker.current_session.detail == "", "Initialization conditions weren't met"
    # assert tracker.current_session.start_time is None, "Initialization conditions weren't met"

    # Act
    window_change = {
        "os": "Ubuntu",
        "pid": 128999,
        "process_name": "Xorg",
        "exe_path": "H:/some/path.exe",
        "window_title": "program_tracker.py - deskSense - Visual Studio Code",
    }
    current_time = UserLocalTime(tracker.user_facing_clock.now())
    new_session = tracker.start_new_session(window_change, current_time)

    # Assert
    clock.now.assert_called_once()
    assert new_session.window_title is not None
    assert new_session.detail is not None
    assert new_session.start_time is not None

    assert not isinstance(new_session, CompletedProgramSession)

    assert new_session.window_title == "Visual Studio Code"
    assert new_session.detail == "program_tracker.py - deskSense"
    assert isinstance(new_session.start_time, UserLocalTime)
    assert new_session.start_time.dt.hour is current_time.dt.hour
    assert new_session.start_time.dt.minute is current_time.dt.minute


def test_window_change_triggers_handler():
    """Test that window changes trigger event handlers"""
    time_from_previous_program = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    t1 = datetime(2024, 1, 1, 12, 2, tzinfo=timezone.utc)
    t2 = datetime(2024, 1, 1, 12, 3, tzinfo=timezone.utc)
    t3 = datetime(2024, 1, 1, 12, 4, tzinfo=timezone.utc)
    t4 = datetime(2024, 1, 1, 12, 7, tzinfo=timezone.utc)
    t5 = datetime(2024, 1, 1, 12, 10, tzinfo=timezone.utc)

    times = [t1, t2, t3, t4, t5]
    clock = MockClock(times)
    clock.now = MagicMock(wraps=clock.now)
    facade = Mock()
    window_change_handler = Mock()

    tracker = ProgramTrackerCore(clock, facade, window_change_handler)

    # Set up facade to yield a window change
    first_test_item = {
        "process_name": "code",
        "window_title": "test.py - Visual Studio Code",
        "os": "Ubuntu",
        "exe_path": "C:/Programs/Program.exe",
    }
    facade.listen_for_window_changes.return_value = iter([first_test_item])

    tracker.user_facing_clock.now.assert_not_called()

    assert tracker.current_session is None, "Initialization condition wasn't met"
    # assert tracker.current_session.window_title == "", "Initialization conditions weren't met"
    # assert tracker.current_session.detail == "", "Initialization conditions weren't met"
    # assert tracker.current_session.start_time is None, "Initialization conditions weren't met"
    # # assert tracker.current_session is None  # Test setup conditions

    # ### Act - Run the tracker
    tracker.run_tracking_loop()
    tracker.user_facing_clock.now.assert_called()
    # There was no session from a prev run so, on_a_different_window is false
    assert tracker.current_session is not None, "Program was still in its init condition"
    assert tracker.current_session.window_title == "Visual Studio Code"
    window_change_handler.assert_called_once()

    session_arg = window_change_handler.call_args[0][0]
    assert isinstance(session_arg, ProgramSession)
    assert hasattr(session_arg, "window_title")
    assert hasattr(session_arg, "productive")

    deliverable = session_arg

    assert deliverable.window_title == "Visual Studio Code"  #
    assert deliverable.detail == "test.py"
    # The second time clock.now() is called, i.e. not 1st window, but the 2nd
    print(deliverable.start_time)
    print(t1)
    assert deliverable.start_time == t1

    # # Continue acting - Need to run the tracking loop again to close a session

    facade.listen_for_window_changes.return_value = [ex3]
    tracker.run_tracking_loop()
    assert tracker.user_facing_clock.now.call_count == 2

    # Verify handler was called with session data
    assert window_change_handler.call_count == 2

    session_arg = window_change_handler.call_args[0][0]
    assert isinstance(session_arg, ProgramSession)
    assert hasattr(session_arg, "window_title")
    assert hasattr(session_arg, "productive")

    deliverable = session_arg

    assert deliverable.window_title == "Google Chrome"  #
    assert deliverable.detail[0:5] == "H&M |"
    # The second time clock.now() is called, i.e. not 1st window, but the 2nd
    assert deliverable.start_time == t2


def test_handle_alt_tab_window():
    """Test handling of 'Alt-tab window' title"""
    clock = MockClock([datetime.now()])
    facade = Mock()
    tracker = ProgramTrackerCore(clock, facade, Mock())

    example = {
        "os": "Ubuntu",
        "pid": 128216,
        "exe_path": "C:/Foo.exe",
        "process_name": "Xorg",
        "window_title": "Alt-tab window",
    }

    time = UserLocalTime(clock.now())

    session = tracker.start_new_session(window_change_dict=example, start_time=time)

    assert session.window_title == "Alt-tab window"


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

    assert tracker.current_session is None, "Initialization conditions not met"

    # Setup
    program1 = {
        "os": "some_val",
        "process_name": "whatever.exe",
        "exe_path": "C:/whatever.exe",
        "window_title": "Alt-tab window",
    }
    facade.listen_for_window_changes.return_value = iter([program1])

    # Act
    tracker.run_tracking_loop()  # 1

    # ### Assert
    assert (
        tracker.current_session is not None
    ), "Tracker wasn't initialized when it should be"
    assert tracker.current_session.window_title == program1["window_title"]
    assert tracker.current_session.detail == no_space_dash_space

    # More setup
    program2 = {
        "os": "some_val",
        "process_name": "whatever5.exe",
        "exe_path": "C:/whatever5.exe",
        "window_title": "rlm@kingdom: ~/Code/deskSense/activitytracker",
    }
    facade.listen_for_window_changes.return_value = iter([program2])
    # Act
    tracker.run_tracking_loop()  # 2

    # ### Assert
    assert tracker.current_session.window_title == program2["window_title"]
    assert tracker.current_session.detail == no_space_dash_space
    assert tracker.current_session.start_time is not None
    assert clock.now.call_count == 2

    # More setup
    program3 = {
        "os": "some_val",
        "process_name": "whatever11.exe",
        "exe_path": "C:/whatever11.exe",
        "window_title": "Vite + React + TS - Google Chrome",
    }
    facade.listen_for_window_changes.return_value = iter([program3])
    # Act
    tracker.run_tracking_loop()

    # Assert
    assert tracker.current_session.window_title == "Google Chrome"
    assert tracker.current_session.detail == "Vite + React + TS"
    assert clock.now.call_count == 3

    # More setup
    program4 = {
        "os": "some_val",
        "process_name": "wherever.exe",
        "exe_path": "C:/wherever.exe",
        "window_title": "Alt-tab window",
    }

    facade.listen_for_window_changes.return_value = iter([program4])
    # Act
    tracker.run_tracking_loop()

    # Assert
    assert tracker.current_session.window_title == program4["window_title"]
    assert clock.now.call_count == 4

    # More setup
    program5 = {
        "os": "some_val",
        "process_name": "whatever25.exe",
        "exe_path": "C:/whatever25.exe",
        "window_title": "program_tracker.py - deskSense - Visual Studio Code",
    }
    facade.listen_for_window_changes.return_value = iter([program5])
    # Act
    tracker.run_tracking_loop()

    # Assert
    assert clock.now.call_count == 5
    assert tracker.current_session.window_title == "Visual Studio Code"

    # ### Final assertions

    assert tracker.current_session.detail == "program_tracker.py - deskSense"
