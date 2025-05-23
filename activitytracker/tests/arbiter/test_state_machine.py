from zoneinfo import ZoneInfo

import pytest

import time
from datetime import datetime, timedelta

from activitytracker.arbiter.state_machine import StateMachine
from activitytracker.object.arbiter_classes import InternalState
from activitytracker.object.classes import ChromeSession, ProgramSession
from activitytracker.util.clock import SystemClock
from activitytracker.util.time_wrappers import UserLocalTime

from ..mocks.mock_clock import MockClock


class TestStateMachine:
    def test_load_first_state(self):

        t1 = datetime.now().astimezone()
        t2 = t1 + timedelta(seconds=4)
        t3 = t2 + timedelta(seconds=8)
        t4 = t3 + timedelta(seconds=10)
        times = [t2, t3]
        clock = MockClock(times)

        asm = StateMachine(clock)
        now = t1
        slightly_later = t2

        # test setup
        assert asm.current_state is None
        assert asm.prior_state is None

        latest_write_at_first_session = UserLocalTime(now)

        first_session = ProgramSession(
            "some/exe/path.exe",
            "path.exe",
            "Visual Studio Code",
            "myfile.py",
            UserLocalTime(now),
        )

        second_session_latest_write = UserLocalTime(slightly_later)

        second = ChromeSession(
            "Claude.ai",
            "How to Cook Chicken Well in Thirty Minutes",
            UserLocalTime(slightly_later),
        )

        # Act
        asm.set_new_session(first_session)
        response = asm.get_concluded_session()

        # None because there IS no prior state to conclude by startign a new session
        assert response is None

        # Act
        asm.set_new_session(second)
        response = asm.get_concluded_session()

        assert response is not None
        assert isinstance(response, ProgramSession)
        assert response.window_title == first_session.window_title
        assert response.start_time == first_session.start_time

    def test_handle_series(self):

        t1 = datetime.now().astimezone()
        t2 = t1 + timedelta(seconds=6)
        t3 = t2 + timedelta(seconds=5)
        t4 = t3 + timedelta(seconds=4)
        t5 = t4 + timedelta(seconds=3)
        times = [t2, t3, t4, t5]

        clock = MockClock(times)

        asm = StateMachine(clock)

        s1_latest = UserLocalTime(t1)
        session1 = ProgramSession(
            "some/path/to/an/exe.exe",
            "exe.exe",
            "Visual Studio Code",
            "myfile.py",
            UserLocalTime(t1),
        )

        s2_latest = UserLocalTime(t2)
        second = ChromeSession(
            "Claude.ai", "How to Cook Chicken Well in Thirty Minutes", UserLocalTime(t2)
        )

        s3_latest = UserLocalTime(t3)
        third = ChromeSession("ChatGPT.com", "Asian Stir Fry Tutorial", UserLocalTime(t3))

        s4_latest = UserLocalTime(t4)
        fourth = ProgramSession(
            "some/path/to/an/exe2.exe",
            "exe2.exe",
            "Postmman",
            "POST requests folder",
            UserLocalTime(t4),
        )

        s5_latest = UserLocalTime(t5)
        fifth = ProgramSession(
            "some/path/to/an/exe4.exe",
            "exe4.exe",
            "Terminal",
            "~/Documents",
            UserLocalTime(t5),
        )

        asm.set_new_session(session1)
        response1 = asm.get_concluded_session()

        assert response1 is None

        asm.set_new_session(second)
        response2 = asm.get_concluded_session()

        assert response2 is not None
        assert isinstance(response2, ProgramSession)
        assert response2.window_title == session1.window_title
        print(t1.strftime("%M:%S"), "\n", t2.strftime("%M:%S"))
        assert response2.start_time == t1

        asm.set_new_session(third)
        response3 = asm.get_concluded_session()

        assert response3 is not None
        assert isinstance(response3, ChromeSession)
        assert response3.domain == second.domain
        assert response3.start_time == t2

        asm.set_new_session(fourth)
        response4 = asm.get_concluded_session()

        assert response4 is not None
        assert isinstance(response4, ChromeSession)
        assert response4.domain == third.domain
        assert response4.start_time == t3

        asm.set_new_session(fifth)
        response5 = asm.get_concluded_session()

        assert response5 is not None
        assert isinstance(response5, ProgramSession)
        assert response5.window_title == fourth.window_title
        assert response5.start_time == t4

        # Verify that the internal stuff is as expected for the unfinished section
        assert asm.current_state is not None
        assert asm.prior_state is not None
        assert isinstance(asm.prior_state, InternalState)
        assert asm.prior_state.session.window_title == fourth.window_title
        assert asm.prior_state.session.start_time == t4

        assert asm.current_state.session.window_title == fifth.window_title
        assert asm.current_state.session.start_time == fifth.start_time

    def test_conclude_without_replacement_at_time(self):
        t1 = datetime.now().astimezone()
        t2 = t1 + timedelta(seconds=6)
        times = [t2]

        clock = MockClock(times)

        state_machine = StateMachine(clock)

        given_conclude_time = UserLocalTime(t2)

        s1_latest = UserLocalTime(t1)
        session1 = ProgramSession(
            "some/path/to/an/exe.exe",
            "exe.exe",
            "Visual Studio Code",
            "myfile.py",
            UserLocalTime(t1),
        )

        # arranging still
        state_machine.set_new_session(session1)

        # act
        concluded_session = state_machine.conclude_without_replacement_at_time(
            given_conclude_time
        )

        assert concluded_session.end_time == given_conclude_time
