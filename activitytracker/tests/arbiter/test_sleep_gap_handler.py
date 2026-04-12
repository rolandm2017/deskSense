from datetime import datetime, timedelta

from activitytracker.arbiter.sleep_gap_handler import SleepGapDecision, SleepGapHandler
from activitytracker.object.classes import ProgramSession
from activitytracker.util.time_wrappers import UserLocalTime


def make_session(start=None):
    start = start or datetime.now().astimezone()
    return ProgramSession(
        "some/exe/path.exe",
        "path.exe",
        "Visual Studio Code",
        "myfile.py",
        UserLocalTime(start),
    )


class FakeSleepDetector:
    def __init__(self, detect_result=(False, None), latest_write=None):
        self._detect_result = detect_result
        self._latest_write = latest_write

    def detect_awakening_from_sleep(self):
        return self._detect_result

    def get_latest_write_time(self):
        return self._latest_write


def test_no_awakening_returns_no_flush_decision():
    handler = SleepGapHandler(FakeSleepDetector(detect_result=(False, None)))

    decision = handler.inspect_before_transition(make_session())

    assert decision == SleepGapDecision(should_flush=False, end_time=None)


def test_awakening_detected_returns_flush_with_gap_time():
    gap_time = UserLocalTime(datetime.now().astimezone() - timedelta(minutes=30))
    handler = SleepGapHandler(
        FakeSleepDetector(detect_result=(True, gap_time))
    )

    decision = handler.inspect_before_transition(make_session())

    assert decision.should_flush is True
    assert decision.end_time == gap_time


def test_suspicious_latest_write_does_not_raise_name_error():
    start = datetime.now().astimezone()
    stale_write = UserLocalTime(start - timedelta(minutes=10))
    handler = SleepGapHandler(
        FakeSleepDetector(detect_result=(False, None), latest_write=stale_write)
    )

    decision = handler.inspect_before_transition(make_session(start))

    assert decision.should_flush is False


def test_recent_latest_write_produces_no_flush():
    start = datetime.now().astimezone()
    recent_write = UserLocalTime(start - timedelta(seconds=5))
    handler = SleepGapHandler(
        FakeSleepDetector(detect_result=(False, None), latest_write=recent_write)
    )

    decision = handler.inspect_before_transition(make_session(start))

    assert decision.should_flush is False
    assert decision.end_time is None
