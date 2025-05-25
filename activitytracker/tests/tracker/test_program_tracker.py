import pytest
from unittest.mock import MagicMock, Mock

from datetime import datetime, timedelta, timezone

from activitytracker.config.definitions import (
    no_space_dash_space,
    productive_apps,
    productive_sites,
)
from activitytracker.object.classes import CompletedProgramSession, ProgramSession
from activitytracker.object.enums import PlayerState
from activitytracker.object.video_classes import VlcInfo
from activitytracker.trackers.program_tracker import ProgramTrackerCore
from activitytracker.util.time_wrappers import UserLocalTime

from ..mocks.mock_clock import MockClock

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

    assert handler.call_count == 1

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
    assert handler.call_count == 2

    # More setup
    program3 = {
        "os": "some_val",
        "process_name": "whatever11.exe",
        "exe_path": "C:/whatever11.exe",
        "window_title": "Vite + React + TS - Some Program",
    }
    facade.listen_for_window_changes.return_value = iter([program3])
    # Act
    tracker.run_tracking_loop()

    # Assert
    assert tracker.current_session.window_title == "Some Program"
    assert tracker.current_session.detail == "Vite + React + TS"
    assert clock.now.call_count == 3
    assert handler.call_count == 3

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
    assert handler.call_count == 4

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
    assert handler.call_count == 5

    # ### Final assertions

    assert tracker.current_session.detail == "program_tracker.py - deskSense"


def test_vlc_info_eq():
    """Testing the custom __eq__ implementation"""
    v1 = VlcInfo("foo", "FOO", "foo", PlayerState.PAUSED)
    v2 = VlcInfo("foo", "FOO", "foo", PlayerState.PAUSED)

    assert v1 == v2


def test_initial_vlc_player_starts_polling():
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

    events = []

    def handler(event):
        events.append(event)

    tracker = ProgramTrackerCore(clock, facade, handler)

    tracker.start_vlc_polling = Mock(wraps=tracker.start_vlc_polling)

    assert tracker.current_session is None, "Initialization conditions not met"

    # Setup
    program1 = {
        "os": "some_val",
        "process_name": "vlc",
        "exe_path": "/usr/bin/vlc",
        "window_title": "How I Got Fluent In French In 30 Days Full 8 Hour Daily Routine -Bue05mPPoFw-1080pp-1705116796.mp4 - VLC media player",
    }
    facade.listen_for_window_changes.return_value = iter([program1])
    try:
        # Act
        tracker.run_tracking_loop()  # 1

        # vlc_media_changed_spy.assert_called_once()

        assert tracker.start_vlc_polling.call_count == 1
        assert tracker.vlc_poller.thread is not None

        # assert isinstance(events[0], ProgramSession)
        # assert isinstance(events[0].video_info, VlcInfo)

        # assert events[0].exe_path == program1["exe_path"]
        # assert events[0].video_info.file == pretend_media.file
    except Exception as e:
        print(e)
        raise e
    finally:
        tracker.stop_vlc_polling()


def test_vlc_is_identified():
    t1 = datetime(2024, 1, 1, 12, 19)

    clock = MockClock([t1])
    facade = Mock()

    def handler(event):
        pass

    tracker = ProgramTrackerCore(clock, facade, handler)

    assert tracker.window_is_vlc({"process_name": "vlc"}) is True


def test_update_vlc_status():
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

    events = []

    def handler(event):
        events.append(event)

    tracker = ProgramTrackerCore(clock, facade, handler)

    tracker.vlc_window = {
        "os": "some_val",
        "process_name": "vlc",
        "exe_path": "/usr/bin/vlc",
        "window_title": "How I Got Fluent In French In 30 Days Full 8 Hour Daily Routine -Bue05mPPoFw-1080pp-1705116796.mp4 - VLC media player",
    }

    vlc_media_changed_spy = Mock(side_effect=tracker.vlc_media_changed)

    tracker.vlc_media_changed = vlc_media_changed_spy
    mock_vlc_infos = [
        VlcInfo(
            "LanguageLords.mov",
            "LanguageLords.mov",
            "C:/Videos/LanguageLords",
            PlayerState.PAUSED,
        ),
        # NOTE that the following two are *identical!*
        VlcInfo(
            "LanguageLords.mov",
            "LanguageLords.mov",
            "C:/Videos/LanguageLords",
            PlayerState.PLAYING,
        ),
        # vlc_media_changed will be FALSE when next entry arrives
        VlcInfo(
            "LanguageLords.mov",
            "LanguageLords.mov",
            "C:/Videos/LanguageLords",
            PlayerState.PLAYING,
        ),
        # New info!
        VlcInfo(
            "LanguageLords.mov",
            "LanguageLords.mov",
            "C:/Videos/LanguageLords",
            PlayerState.PAUSED,
        ),
        # Another duplicate. No change
        VlcInfo(
            "LanguageLords.mov",
            "LanguageLords.mov",
            "C:/Videos/LanguageLords",
            PlayerState.PAUSED,
        ),
    ]

    vlc_tracker_spy = Mock()
    vlc_tracker_spy.side_effect = mock_vlc_infos

    tracker.vlc_tracker.get_updated_vlc_status = vlc_tracker_spy

    # Act
    tracker.update_vlc_status()
    tracker.update_vlc_status()
    tracker.update_vlc_status()
    tracker.update_vlc_status()
    tracker.update_vlc_status()

    # Assert
    assert tracker.vlc_tracker.get_updated_vlc_status.call_count == 5

    assert len(events) == 3
    for event in events:
        assert isinstance(event, ProgramSession)
        assert isinstance(event.video_info, VlcInfo)
        assert event.video_info.file == mock_vlc_infos[0].file

    assert events[0].video_info.player_state == mock_vlc_infos[0].player_state
    # 1 and 1
    assert events[1].video_info.player_state == mock_vlc_infos[1].player_state
    # 1 and 2 - a duplicate
    assert events[1].video_info.player_state == mock_vlc_infos[2].player_state
    # 2 and 3
    assert events[2].video_info.player_state == mock_vlc_infos[3].player_state
    # 2 and 4 - a duplicate
    assert events[2].video_info.player_state == mock_vlc_infos[4].player_state


def test_chrome_is_ignored_without_interrupting():
    """
    Adding "Tracker avoids reporting Google Chrome" caused the tracker to
    fail and quit the first few times I tried it.

    Here, success/fail is tested properly.

    Expect the usual number of handler calls to drop by 1 total for each
    session of Chrome to arrive in the tracker.
    """
    # TODO: Use a facade return value with FOUR values. iter([p1, p2, p3, p4])

    t1 = datetime(2024, 1, 1, 12, 2)
    t2 = datetime(2024, 1, 1, 12, 4)
    t3 = datetime(2024, 1, 1, 12, 7)
    t4 = datetime(2024, 1, 1, 12, 10)
    t5 = datetime(2024, 1, 1, 12, 14)
    t6 = datetime(2024, 1, 1, 12, 15)
    t7 = datetime(2024, 1, 1, 12, 19)

    imaginary_path_to_chrome = "imaginary/path/to/Chrome.exe"

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

    assert handler.call_count == 1

    # More setup

    chrome_one = {
        "os": "Ubuntu",
        "exe_path": imaginary_path_to_chrome,
        "process_name": "chrome",
        "window_title": "Google Docs - Google Chrome",
    }

    facade.listen_for_window_changes.return_value = iter([chrome_one])
    # Act
    tracker.run_tracking_loop()  # 2

    """
    Remember that the clock and handler will not increment when Chrome occurs.
    """

    # ### Assert
    still_program_one = program1["window_title"]
    assert tracker.current_session.window_title == still_program_one

    assert tracker.current_session.detail == no_space_dash_space
    assert tracker.current_session.start_time is not None
    one_chrome_session = 1
    assert clock.now.call_count == 2 - one_chrome_session
    assert handler.call_count == 2 - one_chrome_session

    # More setup
    program3 = {
        "os": "some_val",
        "process_name": "whatever11.exe",
        "exe_path": "C:/whatever11.exe",
        "window_title": "Vite + React + TS - Whatever",
    }
    facade.listen_for_window_changes.return_value = iter([program3])
    # Act
    tracker.run_tracking_loop()

    # Assert
    print(tracker.current_session, "8u239048324324")
    program_three_resulting_title = "Whatever"
    assert tracker.current_session.window_title == program_three_resulting_title
    assert tracker.current_session.detail == "Vite + React + TS"
    assert clock.now.call_count == 3 - one_chrome_session
    assert handler.call_count == 3 - one_chrome_session

    # More setup
    chrome_two = {
        "os": "Ubuntu",
        "pid": 129614,
        "exe_path": imaginary_path_to_chrome,
        "process_name": "chrome",
        "window_title": "Squashing Commits with Git Rebase - Claude - Google Chrome",
    }

    facade.listen_for_window_changes.return_value = iter([chrome_two])
    # Act
    tracker.run_tracking_loop()

    # Assert
    still_program_three = (
        tracker.current_session.window_title == program_three_resulting_title
    )
    assert still_program_three
    two_chrome_sessions = 2
    assert clock.now.call_count == 4 - two_chrome_sessions
    assert handler.call_count == 4 - two_chrome_sessions

    # More setup
    program5 = {
        "os": "some_val",
        "exe_path": "C:/whatever25.exe",
        "process_name": "whatever25.exe",
        "window_title": "program_tracker.py - deskSense - Visual Studio Code",
    }
    facade.listen_for_window_changes.return_value = iter([program5])
    # Act
    tracker.run_tracking_loop()

    # Assert
    assert tracker.current_session.window_title == "Visual Studio Code"
    assert clock.now.call_count == 5 - two_chrome_sessions
    assert handler.call_count == 5 - two_chrome_sessions

    # ### Final assertions

    assert tracker.current_session.detail == "program_tracker.py - deskSense"
