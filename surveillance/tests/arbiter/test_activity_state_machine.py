from xml import dom
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
    """
    Test cases where the machine starts with a Program as the latest state.
    """

    class CurrentStateIsProgram:
        def test_transition_to_different_program(self):
            # Arrange
            now = datetime.now()
            start_session = ProgramSessionData()
            start_session.window_title = "Postman"
            start_session.detail = "GET requests folder"
            start_session.start_time = now
            current_state = ApplicationInternalState(
                "Postman", False, start_session)
            tfpm = TransitionFromProgramMachine(current_state)

            next_session = ProgramSessionData()
            next_session.window_title = "VSCode"
            next_session.detail = "api.py"
            next_session.start_time = now + timedelta(seconds=2)

            # Act
            output = tfpm.compute_next_state(next_session)

            assert isinstance(output, ApplicationInternalState)
            assert output.active_application == next_session.window_title
            assert output.session.detail == next_session.detail
            assert output.is_chrome is False

        def test_transition_to_same_program(self):
            # Arrange
            now = datetime.now()
            start_session = ProgramSessionData()
            start_session.window_title = "Postman"
            start_session.detail = "GET requests folder"
            start_session.start_time = now
            current_state = ApplicationInternalState(
                "Postman", False, start_session)
            tfpm = TransitionFromProgramMachine(current_state)

            next_session = ProgramSessionData()
            next_session.window_title = "Postman"
            next_session.detail = "GET requests folder"
            next_session.start_time = now + timedelta(seconds=2)

            # Act
            output = tfpm.compute_next_state(next_session)

            assert isinstance(output, ApplicationInternalState)
            assert output.active_application == next_session.window_title
            assert output.session.detail == next_session.detail
            assert output.is_chrome is False

        def test_transition_to_chrome(self):
            # Arrange
            now = datetime.now()
            start_session = ProgramSessionData()
            start_session.window_title = "Postman"
            start_session.detail = "GET requests folder"
            start_session.start_time = now
            current_state = ApplicationInternalState(
                "Postman", False, start_session)
            tfpm = TransitionFromProgramMachine(current_state)

            next_session = ChromeSessionData()
            next_session.domain = "Google.com"
            next_session.detail = "Search here"
            next_session.start_time = now + timedelta(seconds=2)

            # Act
            output = tfpm.compute_next_state(next_session)

            assert isinstance(output, ChromeInternalState)
            assert output.session.domain == next_session.domain
            assert output.session.detail == next_session.detail
            assert output.is_chrome is True

    class CurrentStateIsChrome:
        """
        Test cases where the machine starts with Chrome as the latest state.
        """

        def test_start_with_chrome(self):
            """A sad path. Should not happen, constitutes a bug."""
            now = datetime.now()

            chrome_tab = ChromeSessionData()
            chrome_tab.domain = "Claude.ai"
            chrome_tab.detail = "Baking tips"
            chrome_tab.start_time = now
            current_state = ChromeInternalState(
                "Chrome", True, "Claude.ai", chrome_tab)

            # Use pytest's raises context manager
            with pytest.raises(TypeError, match="requires an ApplicationInternalState"):
                tfpm = TransitionFromProgramMachine(current_state)


class TestTransitionFromChrome:
    class CurrentStateIsProgram:
        """
        Test cases where the machine starts with a Program as the latest state.
        """

        def test_start_from_program(self):
            """A sad path"""
            session = ProgramSessionData()
            session.window_title = "VSCode"
            session.detail = "test_my_wonerful_code.py"
            session.start_time = datetime.now()
            current_state = ApplicationInternalState("VSCode", False, session)

            with pytest.raises(TypeError, match="requires a ChromeInternalState"):
                tfcm = TransitionFromChromeMachine(current_state)

    class CurrentStateIsChrome:
        """
        Test cases where the machine starts with Chrome as the latest state.
        """

        def test_transition_to_program(self):
            now = datetime.now()

            start_session = ChromeSessionData()
            start_session.domain = "ChatGPT.com"
            start_session.detail = "American stir fry"
            start_session.start_time = now
            current_state = ChromeInternalState(
                "Chrome", True, "ChatGPT.com", start_session)

            tfcm = TransitionFromChromeMachine(current_state)

            next_session = ProgramSessionData()
            next_session.window_title = "Postman"
            next_session.detail = "GET requests folder"
            next_session.start_time = now + timedelta(seconds=4)

            output = tfcm.compute_next_state(next_session)

            assert isinstance(output, ApplicationInternalState)
            assert output.active_application == next_session.window_title
            assert output.session.detail == next_session.detail

        def test_transition_to_another_tab(self):
            now = datetime.now()

            domain = "ChatGPT.com"
            start_session = ChromeSessionData()
            start_session.domain = domain
            start_session.detail = "American stir fry"
            start_session.start_time = now
            current_state = ChromeInternalState(
                "Chrome", True, domain, start_session)

            tfcm = TransitionFromChromeMachine(current_state)

            next_session = ChromeSessionData()
            next_session.domain = "Twitter.com"
            next_session.detail = "Home"
            next_session.start_time = now + timedelta(seconds=10)

            output = tfcm.compute_next_state(next_session)

            assert isinstance(output, ChromeInternalState)
            assert output.current_tab == next_session.domain
            assert output.session.detail == next_session.detail

        def test_transition_to_same_tab(self):
            now = datetime.now()
            later = now + timedelta(seconds=10)

            domain = "Facebook.com"
            start_session = ChromeSessionData()
            start_session.domain = domain
            start_session.detail = "Home"
            start_session.start_time = now
            current_state = ChromeInternalState(
                "Chrome", True, domain, start_session)

            tfcm = TransitionFromChromeMachine(current_state)

            next_session = ChromeSessionData()
            next_session.domain = domain
            next_session.detail = "Marketplace"
            next_session.start_time = later

            output = tfcm.compute_next_state(next_session)

            assert isinstance(output, ChromeInternalState)
            assert output.current_tab == domain
            assert output.session.start_time == now  # NOT later.
