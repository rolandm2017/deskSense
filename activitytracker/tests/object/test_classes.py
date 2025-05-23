import pytest

import pytz
from datetime import datetime

from activitytracker.object.classes import (
    ChromeSession,
    CompletedChromeSession,
    CompletedProgramSession,
    ProgramSession,
    SessionLedger,
)
from activitytracker.object.video_classes import VlcInfo
from activitytracker.util.errors import SessionClosedError
from activitytracker.util.time_wrappers import UserLocalTime

tz_for_test = "Asia/Tokyo"
tokyo_tz = pytz.timezone(tz_for_test)


def test_ledger_init():
    ledger = SessionLedger("test_ledger")
    assert ledger.get_total() == 0
    assert ledger.open is True


def test_ledger_add_ten_sec():
    ledger = SessionLedger("test_ledger")

    ledger.add_ten_sec()
    assert ledger.get_total() == 10
    ledger.add_ten_sec()
    assert ledger.get_total() == 20


def test_ledger_deduct_time():
    ledger = SessionLedger("test_ledger")

    ledger.add_ten_sec()
    ledger.add_ten_sec()
    assert ledger.get_total() == 20

    ledger.extend_by_n(4)

    assert ledger.open is False

    assert ledger.get_total() == 20 + 4


def test_cant_add_time_after_ledger_closure():
    ledger = SessionLedger("test_ledger")

    ledger.add_ten_sec()
    ledger.add_ten_sec()

    ledger.extend_by_n(8)

    assert ledger.open is False

    with pytest.raises(SessionClosedError):
        ledger.add_ten_sec()


def test_program_session_constructor():
    path = "C:/ProgramFiles/foo.exe"
    process = "foo.exe"
    window_title = "The Foo Program"
    detail = "Get Your Foo"
    start_time = UserLocalTime(tokyo_tz.localize(datetime(2025, 4, 29, 10, 23, 0)))
    session = ProgramSession(path, process, window_title, detail, start_time)

    assert session.exe_path == path
    assert session.process_name == process
    assert session.window_title == window_title
    assert session.detail == detail
    assert session.start_time.dt == start_time.dt
    assert session.duration is None
    assert session.end_time is None


def test_chrome_session_constructor():
    pass


def test_to_completed():
    path = "C:/ProgramFiles/foo.exe"
    process = "foo.exe"
    window_title = "The Foo Program"
    detail = "Get Your Foo"
    start_time = UserLocalTime(tokyo_tz.localize(datetime(2025, 4, 29, 10, 23, 0)))
    session = ProgramSession(path, process, window_title, detail, start_time)

    # Give the session ledger some time
    session.ledger.add_ten_sec()
    session.ledger.add_ten_sec()
    session.ledger.add_ten_sec()

    end_time = UserLocalTime(tokyo_tz.localize(datetime(2025, 4, 29, 10, 25, 25)))
    completed = session.to_completed(end_time)

    assert completed.exe_path == path
    assert completed.process_name == process
    assert completed.window_title == window_title
    assert completed.detail == detail
    assert completed.start_time.dt == start_time.dt
    assert completed.end_time.dt == end_time.dt
    assert (
        completed.duration.total_seconds() == (end_time.dt - start_time.dt).total_seconds()
    )

    # Test the ledger
    assert completed.ledger.get_total() == 30

    # It still works
    completed.ledger.add_ten_sec()
    assert completed.ledger.get_total() == 40


def test_add_duration_for_tests():
    path = "C:/ProgramFiles/foo.exe"
    process = "foo.exe"
    window_title = "The Foo Program"
    detail = "Get Your Foo"
    start_time = UserLocalTime(tokyo_tz.localize(datetime(2025, 4, 29, 10, 23, 0)))
    end_time = UserLocalTime(tokyo_tz.localize(datetime(2025, 4, 29, 10, 25, 55)))

    video_info = VlcInfo("file.mov", "file.mov", "C:/movies", "playing")

    premade_duration = end_time.dt - start_time.dt

    session = CompletedProgramSession(
        path,
        process,
        window_title,
        detail,
        video_info,
        start_time,
        end_time,
        True,
        premade_duration,
    )

    assert session.duration.total_seconds() == premade_duration.total_seconds()
