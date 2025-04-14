
import pytest

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import time

from surveillance.src.arbiter.activity_state_machine import ActivityStateMachine, TransitionFromChromeMachine, TransitionFromProgramMachine
from surveillance.src.object.classes import ChromeSessionData, ProgramSessionData
from surveillance.src.util.clock import SystemClock
from surveillance.src.db.models import ChromeTab
from surveillance.src.object.arbiter_classes import ApplicationInternalState, ChromeInternalState

from ..mocks.mock_clock import MockClock


class TestActivityStateMachine:
    def test_load_first_state(self):

        t1 = datetime.now().astimezone()
        t2 = t1 + timedelta(seconds=4)
        t3 = t2 + timedelta(seconds=8)
        t4 = t3 + timedelta(seconds=10)
        times = [t2, t3]
        clock = MockClock(times)

        asm = ActivityStateMachine(clock)
        now = t1
        slightly_later = t2

        # test setup
        assert asm.current_state is None
        assert asm.prior_state is None

        first_session = ProgramSessionData("Visual Studio Code", "myfile.py", now)

        second = ChromeSessionData("Claude.ai","How to Cook Chicken Well in Thirty Minutes", slightly_later)

        # Act
        asm.set_new_session(first_session)
        response = asm.get_concluded_session()

        # None because there IS no prior state to conclude by startign a new session
        assert response is None

        # Act
        asm.set_new_session(second)
        response = asm.get_concluded_session()

        assert response is not None
        assert response.window_title == first_session.window_title
        assert response.window_title == first_session.window_title
        assert response.start_time == first_session.start_time
        assert response.end_time is not None
        # Might not always work out so neatly:
        assert response.end_time == second.start_time

        assert response.end_time == slightly_later

    def test_handle_series(self):

        t1 = datetime.now().astimezone()
        t2 = t1 + timedelta(seconds=6)
        t3 = t2 + timedelta(seconds=5)
        t4 = t3 + timedelta(seconds=4)
        t5 = t4 + timedelta(seconds=3)
        times = [t2, t3, t4, t5]

        clock = MockClock(times)

        asm = ActivityStateMachine(clock)

        session1 = ProgramSessionData("Visual Studio Code", "myfile.py", t1)

        second = ChromeSessionData("Claude.ai", "How to Cook Chicken Well in Thirty Minutes", t2)

        third = ChromeSessionData("ChatGPT.com", "Asian Stir Fry Tutorial", t3)

        fourth = ProgramSessionData("Postmman", "POST requests folder", t4)

        fifth = ProgramSessionData("Terminal", "~/Documents", t5)

        asm.set_new_session(session1)
        response1 = asm.get_concluded_session()

        assert response1 is None

        asm.set_new_session(second)
        response2 = asm.get_concluded_session()

        assert response2 is not None
        assert isinstance(response2, ProgramSessionData)
        assert response2.window_title == session1.window_title
        print(t1.strftime('%M:%S'), "\n", t2.strftime('%M:%S'))
        assert response2.start_time == t1
        assert response2.end_time is not None
        assert response2.end_time != t1
        assert response2.end_time == t2

        asm.set_new_session(third)
        response3 = asm.get_concluded_session()

        assert response3 is not None
        assert isinstance(response3, ChromeSessionData)
        assert response3.domain == second.domain
        assert response3.start_time == t2
        assert response3.end_time is not None
        assert response3.end_time != t2
        assert response3.end_time == t3

        asm.set_new_session(fourth)
        response4 = asm.get_concluded_session()

        assert response4 is not None
        assert isinstance(response4, ChromeSessionData)
        assert response4.domain == third.domain
        assert response4.start_time == t3
        assert response4.end_time is not None
        assert response4.end_time == t4

        asm.set_new_session(fifth)
        response5 = asm.get_concluded_session()

        assert response5 is not None
        assert isinstance(response5, ProgramSessionData)
        assert response5.window_title == fourth.window_title
        assert response5.start_time == t4
        assert response5.end_time is not None
        assert response5.end_time == t5

        # Verify that the internal stuff is as expected for the unfinished section
        assert asm.current_state is not None
        assert asm.prior_state is not None
        assert isinstance(asm.prior_state, ApplicationInternalState)
        assert asm.prior_state.active_application == fourth.window_title
        assert asm.prior_state.session.start_time == t4

        assert asm.current_state.active_application == fifth.window_title
        assert asm.current_state.session.start_time == fifth.start_time


class TestTransitionFromProgram:
    """
    Test cases where the Transition From Program Machine.
    """

    def test_transition_to_different_program(self):
        # Arrange
        clock = SystemClock()
        now = clock.now()
        start_session = ProgramSessionData()
        start_session.window_title = "Postman"
        start_session.detail = "GET requests folder"
        start_session.start_time = now
        current_state = ApplicationInternalState(
            "Postman", False, start_session)
        assert isinstance(current_state, ApplicationInternalState)
        tfpm = TransitionFromProgramMachine(current_state)

        next_session = ProgramSessionData()
        next_session.window_title = "PyCharm"
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
        system_clock = SystemClock()

        now = system_clock.now()
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
        system_clock = SystemClock()

        now = system_clock.now()
        start_session = ProgramSessionData()
        start_session.window_title = "Postman"
        start_session.detail = "GET requests folder"
        start_session.start_time = now
        current_state = ApplicationInternalState(
            "Postman", False, start_session)
        tfpm = TransitionFromProgramMachine(current_state)

        next_session = ChromeSessionData("Google.com", "Search here", now + timedelta(seconds=2))

        # Act
        output = tfpm.compute_next_state(next_session)

        assert isinstance(output, ChromeInternalState)
        assert output.session.domain == next_session.domain
        assert output.session.detail == next_session.detail
        assert output.is_chrome is True

    def test_start_with_chrome(self):
        """
        Test cases where the machine starts with Chrome as the latest state.

        A sad path. Should not happen, constitutes a bug.
        """
        system_clock = SystemClock()
        now = system_clock.now()

        chrome_tab = ChromeSessionData("Claude.ai", "Baking tips", now)
        current_state = ChromeInternalState(
            "Chrome", True, "Claude.ai", chrome_tab)

        # Use pytest's raises context manager
        with pytest.raises(TypeError, match="requires an ApplicationInternalState"):
            tfpm = TransitionFromProgramMachine(current_state)


class TestTransitionFromChrome:
    """
    Test cases for the Transition From Chrome Machine.
    """

    def test_start_from_program(self):
        """A sad path. Machine cannot start with ApplicationInternalState, by design."""
        system_clock = SystemClock()

        session = ProgramSessionData("PyCharm", "test_my_wonerful_code.py", system_clock.now())
        current_state = ApplicationInternalState("PyCharm", False, session)

        with pytest.raises(TypeError, match="requires a ChromeInternalState"):
            tfcm = TransitionFromChromeMachine(current_state)

    """
    Test cases where the machine starts with Chrome as the latest state.
    """

    def test_transition_to_program(self):
        system_clock = SystemClock()

        now = system_clock.now()

        start_session = ChromeSessionData("ChatGPT.com", "American stir fry", now)
        current_state = ChromeInternalState("Chrome", True, "ChatGPT.com", start_session)

        tfcm = TransitionFromChromeMachine(current_state)

        next_session = ProgramSessionData("Postman", "GET requests folder", now + timedelta(seconds=4))

        output = tfcm.compute_next_state(next_session)

        assert isinstance(output, ApplicationInternalState)
        assert output.active_application == next_session.window_title
        assert output.session.detail == next_session.detail

    def test_transition_to_another_tab(self):
        system_clock = SystemClock()

        now = system_clock.now()

        domain = "ChatGPT.com"
        start_session = ChromeSessionData(domain, "American stir fry", now)
        current_state = ChromeInternalState(
            "Chrome", True, domain, start_session)

        tfcm = TransitionFromChromeMachine(current_state)

        next_session = ChromeSessionData("Twitter.com", "Home", now + timedelta(seconds=10))

        output = tfcm.compute_next_state(next_session)

        assert isinstance(output, ChromeInternalState)
        assert output.current_tab == next_session.domain
        assert output.session.detail == next_session.detail

    def test_transition_to_same_tab(self):
        system_clock = SystemClock()

        now = system_clock.now()
        later = now + timedelta(seconds=10)

        domain = "Facebook.com"
        start_session = ChromeSessionData(domain, "Home", now)
        current_state = ChromeInternalState(
            "Chrome", True, domain, start_session)

        tfcm = TransitionFromChromeMachine(current_state)

        next_session = ChromeSessionData(domain, "Marketplace", later)

        output = tfcm.compute_next_state(next_session)

        assert isinstance(output, ChromeInternalState)
        assert output.current_tab == domain
        assert output.session.start_time == now  # NOT later.
