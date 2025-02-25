import pytest

from datetime import datetime, timedelta

from src.arbiter.activity_state_machine import ActivityStateMachine, TransitionFromChromeMachine, TransitionFromProgramMachine
from src.object.classes import ChromeSessionData, ProgramSessionData
from src.util.clock import SystemClock
from surveillance.src.db.models import ChromeTab
from surveillance.src.object.arbiter_classes import ApplicationInternalState, ChromeInternalState


class TestActivityStateMachine:
    def test_load_first_state(self):
        clock = SystemClock()
        asm = ActivityStateMachine(clock)
        now = datetime.now()
        slightly_later = now + timedelta(seconds=6)

        # test setup
        assert asm.current_state is None
        assert asm.prior_state is None

        first_session = ProgramSessionData()
        first_session.window_title = "Visual Studio Code"
        first_session.detail = "myfile.py"
        first_session.start_time = now

        second = ChromeSessionData()
        second.domain = "Claude.ai"
        second.detail = "How to Cook Chicken Well in Thirty Minutes"
        second.start_time = slightly_later

        # Act
        asm.set_new_session(first_session)
        response = asm.get_finished_state()

        # None because there IS no prior state to conclude by startign a new session
        assert response is None

        # Act
        asm.set_new_session(second)
        response = asm.get_finished_state()

        assert response is not None
        assert response.active_application == first_session.window_title
        assert response.session.window_title == first_session.window_title

        assert response.session.end_time == slightly_later

    def test_handle_series(self):
        clock = SystemClock()
        asm = ActivityStateMachine(clock)
        t1 = datetime.now()
        t2 = t1 + timedelta(seconds=6)
        t3 = t2 + timedelta(seconds=5)
        t4 = t3 + timedelta(seconds=4)
        t5 = t4 + timedelta(seconds=3)

        session1 = ProgramSessionData()
        session1.window_title = "Visual Studio Code"
        session1.detail = "myfile.py"
        session1.start_time = t1

        second = ChromeSessionData()
        second.domain = "Claude.ai"
        second.detail = "How to Cook Chicken Well in Thirty Minutes"
        second.start_time = t2

        third = ChromeSessionData()
        third.domain = "ChatGPT.com"
        third.detail = "Asian Stir Fry Tutorial"
        third.start_time = t3

        fourth = ProgramSessionData()
        fourth.window_title = "Postmman"
        fourth.detail = "POST requests folder"
        fourth.start_time = t4

        fifth = ProgramSessionData()
        fifth.window_title = "Terminal"
        fifth.detail = "~/Documents"
        fifth.start_time = t5

        asm.set_new_session(session1)
        response1 = asm.get_finished_state()

        assert response1 is None

        asm.set_new_session(second)
        response2 = asm.get_finished_state()

        assert response2 is not None
        assert isinstance(response2, ApplicationInternalState)
        assert response2.active_application == session1.window_title
        assert response2.session.start_time == t1
        assert response2.session.end_time is not None
        assert response2.session.end_time == t2

        asm.set_new_session(third)
        response3 = asm.get_finished_state()

        assert response3 is not None
        assert isinstance(response3, ChromeInternalState)
        assert response3.session.domain == second.domain
        assert response3.session.start_time == t2
        assert response3.session.end_time is not None
        assert response3.session.end_time == t3

        asm.set_new_session(fourth)
        response4 = asm.get_finished_state()

        assert response4 is not None
        assert isinstance(response4, ChromeInternalState)
        assert response4.session.domain == third.domain
        assert response4.session.start_time == t3
        assert response4.session.end_time is not None
        assert response4.session.end_time == t4

        asm.set_new_session(fifth)
        response5 = asm.get_finished_state()

        assert response5 is not None
        assert isinstance(response5, ApplicationInternalState)
        assert response5.active_application == fourth.window_title
        assert response5.session.start_time == t4
        assert response5.session.end_time is not None
        assert response5.session.end_time == t5

        # Verify that the internal stuff is as expected for the unfinished section
        assert asm.program_state.active_application == fifth.window_title
        assert asm.program_state.session.start_time == fifth.start_time


class TestTransitionFromProgram:
    class CurrentStateIsProgram:
        """
        Test cases where the machine starts with a Program as the latest state.
        """

        def test_foo(self):
            session = ProgramSessionData()
            session.window_title = "Postman"
            session.detail = "GET requests folder"
            session.start_time = datetime.now()
            current_state = ApplicationInternalState("Postman", False, session)
            pass

    class CurrentStateIsChrome:
        """
        Test cases where the machine starts with Chrome as the latest state.
        """

        def test_bar(self):
            chrome_tab = ChromeSessionData()
            chrome_tab.domain = "Claude.ai"
            chrome_tab.detail = "Baking tips"
            chrome_tab.start_time = datetime.now()
            current_state = ChromeInternalState(
                "Chrome", True, "Claude.ai", chrome_tab)
            pass


class TestTransitionFromChrome:
    class CurrentStateIsProgram:
        """
        Test cases where the machine starts with a Program as the latest state.
        """

        def test_foo(self):
            session = ProgramSessionData()
            session.window_title = "VSCode"
            session.detail = "test_my_wonerful_code.py"
            session.start_time = datetime.now()
            current_state = ApplicationInternalState("VSCode", False, session)
            pass

    class CurrentStateIsChrome:
        """
        Test cases where the machine starts with Chrome as the latest state.
        """

        def test_bar(self):
            chrome_tab = ChromeSessionData()
            chrome_tab.domain = "Claude.ai"
            chrome_tab.detail = "Baking tips"
            chrome_tab.start_time = datetime.now()
            current_state = ChromeInternalState(
                "Chrome", True, "ChatGPT.com", chrome_tab)
            pass
