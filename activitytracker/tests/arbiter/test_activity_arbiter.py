from datetime import datetime, timedelta

from activitytracker.arbiter.activity_arbiter import ActivityArbiter
from activitytracker.object.classes import ChromeSession, ProgramSession
from activitytracker.util.time_wrappers import UserLocalTime

from ..mocks.fake_persistence import FakeSystemStatusDao
from ..mocks.mock_clock import MockClock
from ..mocks.mock_engine_container import DeterministicPulseContainer


def make_arbiter_with_no_sleep():
    t1 = datetime.now().astimezone()
    t2 = t1 + timedelta(seconds=4)
    clock = MockClock([t1, t2])
    return ActivityArbiter(clock, FakeSystemStatusDao(), DeterministicPulseContainer([]))


def make_program_session(start_time):
    return ProgramSession(
        "some/exe/path.exe",
        "path.exe",
        "Visual Studio Code",
        "myfile.py",
        UserLocalTime(start_time),
    )


def make_chrome_session(start_time):
    return ChromeSession(
        "Claude.ai",
        "How to Cook Chicken Well in Thirty Minutes",
        UserLocalTime(start_time),
    )


def test_first_session_is_initialization():
    arbiter = make_arbiter_with_no_sleep()
    t1 = datetime.now().astimezone()
    session_a = make_program_session(t1)

    outcome = arbiter._advance_state(session_a)

    assert outcome.was_initialization is True
    assert outcome.concluded_session is None
    assert outcome.new_session == session_a


def test_second_session_concludes_first():
    arbiter = make_arbiter_with_no_sleep()
    t1 = datetime.now().astimezone()
    t2 = t1 + timedelta(seconds=4)
    session_a = make_program_session(t1)
    session_b = make_chrome_session(t2)

    arbiter._advance_state(session_a)
    outcome = arbiter._advance_state(session_b)

    assert outcome.was_initialization is False
    assert outcome.concluded_session is not None
    assert outcome.concluded_session.start_time == session_a.start_time
    assert outcome.new_session == session_b
