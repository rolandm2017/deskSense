from datetime import timedelta


from surveillance.object.classes import ChromeSession, ProgramSession, CompletedChromeSession, CompletedProgramSession
from surveillance.object.arbiter_classes import ChromeInternalState, ApplicationInternalState, InternalState
from surveillance.util.program_tools import window_is_chrome
from surveillance.util.console_logger import ConsoleLogger
from surveillance.util.copy_util import snapshot_obj_for_tests
from surveillance.util.time_wrappers import UserLocalTime


class ActivityStateMachine:
    def __init__(self, user_facing_clock):
        """
        Is a finite state machine.

        One instance per user. Meaning, state from User A has no reason to interact with User B's state.
        """
        self.user_facing_clock = user_facing_clock
        self.current_state: InternalState | None = None
        self.prior_state: InternalState | None = None
        self.transition_from_program = self._initialize_program_machine()
        self.transition_from_chrome = self._initialize_chrome_machine()
        self.state_listeners = []
        self.logger = ConsoleLogger()

    def set_new_session(self, next_session: ProgramSession | ChromeSession):
        # FIXME:
        # FIXME: Isn't this JUST handing off one session to the other now?
        # FIXME: Existing just to do, "end_time - start_time" and such
        # FIXME:
        next_session = snapshot_obj_for_tests(next_session)
        if self.current_state:
            prior_update_was_program = isinstance(
                self.current_state, ApplicationInternalState)
            if prior_update_was_program:
                updated_state = self.transition_from_program.compute_next_state(
                    next_session)
                # updated_overall_state = OverallState()
            else:
                updated_state = self.transition_from_chrome.compute_next_state(
                    next_session)
            if next_session.start_time:

                self._conclude_session(
                    self.current_state, next_session.start_time)
                self.prior_state = self.current_state
                self.current_state = updated_state
            else:
                print("Error:", next_session)
                raise ValueError("Session start time was None")

        else:
            # No current state yet, this is initialization:
            if isinstance(next_session, ProgramSession):
                is_chrome = window_is_chrome(next_session.window_title)
                updated_state = ApplicationInternalState(
                    next_session.window_title, is_chrome, next_session)
            else:
                updated_state = ChromeInternalState(
                    "Chrome", True, next_session.domain, next_session)
            self.current_state = updated_state

    @staticmethod
    def is_initialization_session(some_dict):
        """Asks 'is it an empty dict?'"""
        return isinstance(some_dict, dict) and not some_dict

    def _conclude_session(self, state: InternalState, incoming_session_start: UserLocalTime):
        if not isinstance(incoming_session_start, UserLocalTime):
            raise ValueError("Expected a UserLocalTime")
        if self.is_initialization_session(state.session):
            return

        duration = incoming_session_start - state.session.start_time

        session_copy = snapshot_obj_for_tests(state.session)

        completed = session_copy.to_completed(incoming_session_start)
        completed.duration = duration

        state.session = completed

    @staticmethod
    def _initialize(first_session):
        if isinstance(first_session, ProgramSession):
            is_chrome = window_is_chrome(first_session.window_title)
            updated_state = ApplicationInternalState(
                first_session.window_title, is_chrome, first_session)
        else:
            assert isinstance(first_session, ChromeSession)
            updated_state = ChromeInternalState(
                "Chrome", True, first_session.domain, first_session)
        return updated_state

    @staticmethod
    def _initialize_program_machine():
        start_state = ApplicationInternalState("", "", {})
        return TransitionFromProgramMachine(
            start_state)

    @staticmethod
    def _initialize_chrome_machine():
        start_state = ChromeInternalState("", "", "", {})
        return TransitionFromChromeMachine(
            start_state)

    def get_concluded_session(self) -> CompletedProgramSession | CompletedChromeSession | None:
        """Assumes the prior state is the updated transformation from set_new_session"""
        on_initialization = self.prior_state is None
        if on_initialization:
            return None
        assert self.prior_state is not None
        return self.prior_state.session

    def conclude_without_replacement(self):
        """For wrap up when the computer is powering off to avoid sessions left open"""
        if self.current_state is None:
            return  # Nothing to wrap up
        end_time = UserLocalTime(self.user_facing_clock.now())
        assert isinstance(end_time, UserLocalTime)
        self._conclude_session(self.current_state, end_time)
        session_for_daos = self.current_state.session
        self.current_state = None  # Reset for power back on
        return session_for_daos


class TransitionFromProgramMachine:
    def __init__(self, current_state):
        if not isinstance(current_state, ApplicationInternalState):
            raise TypeError(
                "TransitionFromProgramMachine requires an ApplicationInternalState")

        self.current_state = current_state

    def compute_next_state(self, next_state: ProgramSession | ChromeSession) -> InternalState:
        if isinstance(next_state, ProgramSession):
            return self._change_to_new_program(next_state)
        else:
            return self._transit_to_chrome_state(next_state)

    def _change_to_new_program(self, next_session: ProgramSession) -> ApplicationInternalState:
        # TODO: If next state is the same program, return current state
        is_same_program = self.current_state.active_application == next_session.window_title
        if is_same_program:
            return self._stay_on_same_program()
        else:
            # Program A -> Program B, neither is Chrome
            # Create a new state that is on a different program
            is_chrome = False
            current_tab = None
            brand_new_state = ApplicationInternalState(
                next_session.window_title, is_chrome, next_session)
            return brand_new_state

    def _stay_on_same_program(self) -> ApplicationInternalState:
        return self.current_state  # No change needed

    @staticmethod
    def _transit_to_chrome_state(next_session: ChromeSession) -> ChromeInternalState:
        # FIXME: What to do with the case where, where, there is a new Chrome opening?
        # A new tab opens at the same time as Chrome opens.
        # FIXME: What to do with, case where, a tab was suspended in the bg
        # while user ran VSCode, now he goes back to Claude?
        next_state = ChromeInternalState(active_application="Chrome",
                                         is_chrome=True,
                                         current_tab=next_session.domain,
                                         session=next_session)
        return next_state


class TransitionFromChromeMachine:
    def __init__(self,  current_state):

        if not isinstance(current_state, ChromeInternalState):
            raise TypeError(
                "TransitionFromChromeMachine requires a ChromeInternalState")

        self.current_state = current_state

    def compute_next_state(self, next_session: ProgramSession | ChromeSession) -> InternalState:
        if isinstance(next_session, ProgramSession):
            return self._transit_to_program(next_session)
        else:
            return self._handle_change_tabs(next_session)

    def _transit_to_program(self, next_session: ProgramSession) -> InternalState:
        now_on_regular_app = not window_is_chrome(next_session.window_title)
        if now_on_regular_app:
            return self._change_to_new_program(next_session)
        else:
            return self._stay_on_chrome()  # Still on Chrome - Pass

    def _handle_change_tabs(self, next_session: ChromeSession) -> ChromeInternalState:
        on_different_tab = self.current_state.current_tab != next_session.domain
        if on_different_tab:
            return self._change_to_new_tab(next_session)
        else:
            return self._stay_on_current_tab()

    @staticmethod
    def _change_to_new_program(next_session: ProgramSession) -> ApplicationInternalState:
        # TODO: How to implement changing the program?
        # Create a new state that is a Program state
        is_chrome = False
        current_tab = None  # should it be whatever is open in chrome? if Chrome is open
        next_state = ApplicationInternalState(
            next_session.window_title, is_chrome, next_session)
        return next_state

    def _stay_on_chrome(self) -> ChromeInternalState:
        return self.current_state  # Explicitly stay the same

    @staticmethod
    def _change_to_new_tab(next_session: ChromeSession) -> ChromeInternalState:
        next_state = ChromeInternalState(active_application="Chrome",
                                         is_chrome=True,
                                         current_tab=next_session.domain,
                                         session=next_session)
        return next_state

    def _stay_on_current_tab(self) -> ChromeInternalState:
        # Chrome, currentDomain -> Chrome, currentDomain
        # "Skip over" this state change.
        return self.current_state  # Explicitly keep the same object as state
