from datetime import datetime

import pytest

from activitytracker.arbiter.activity_notifier import ActivityNotifier
from activitytracker.object.classes import ProgramSession
from activitytracker.util.time_wrappers import UserLocalTime


def make_session(title="Visual Studio Code"):
    return ProgramSession(
        "some/exe/path.exe",
        "path.exe",
        title,
        "myfile.py",
        UserLocalTime(datetime.now().astimezone()),
    )


class RecorderSpy:
    def __init__(self):
        self.state_changed_calls = []
        self.new_session_calls = []

    def on_state_changed(self, session):
        self.state_changed_calls.append(session)

    def on_new_session(self, session):
        self.new_session_calls.append(session)


def test_ui_listener_fires_on_display_update():
    notifier = ActivityNotifier()
    calls = []
    notifier.add_ui_listener(calls.append)

    session = make_session()
    notifier.notify_display_update(session)

    assert calls == [session]


def test_display_update_is_noop_without_listener():
    notifier = ActivityNotifier()
    notifier.notify_display_update(make_session())  # must not raise


def test_add_recorder_listener_rejects_missing_on_state_changed():
    notifier = ActivityNotifier()
    with pytest.raises(AttributeError):
        notifier.add_recorder_listener(object())


def test_notify_new_session_snapshots_session():
    notifier = ActivityNotifier()
    spy = RecorderSpy()
    notifier.add_recorder_listener(spy)

    session = make_session("Original")
    notifier.notify_new_session(session)
    session.window_title = "Mutated"

    assert len(spy.new_session_calls) == 1
    assert spy.new_session_calls[0].window_title == "Original"


def test_notify_completed_session_passes_none_through():
    notifier = ActivityNotifier()
    spy = RecorderSpy()
    notifier.add_recorder_listener(spy)

    notifier.notify_completed_session(None)

    assert spy.state_changed_calls == [None]


def test_notify_completed_session_noop_without_recorder():
    notifier = ActivityNotifier()
    notifier.notify_completed_session(None)  # must not raise


def test_recorder_property_returns_registered_listener():
    notifier = ActivityNotifier()
    spy = RecorderSpy()
    notifier.add_recorder_listener(spy)

    assert notifier.recorder is spy
