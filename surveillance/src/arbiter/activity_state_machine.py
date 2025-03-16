from datetime import timedelta


from ..object.classes import ChromeSessionData, ProgramSessionData
from ..object.arbiter_classes import ChromeInternalState, ApplicationInternalState, InternalState
from ..util.program_tools import window_is_chrome
from ..util.errors import MismatchedTimezonesError, SuspiciousDurationError, TimezoneUnawareError
from ..util.console_logger import ConsoleLogger


# class OverallState:
#     def __init__(self):
#         self.program_state = None
#         self.chrome_state = None
#         self.latest_update = None


class ActivityStateMachine:
    def __init__(self, user_facing_clock):
        """
        Is a finite state machine.

        One instance per user. Meaning, state from User A has no reason to interact with User B's state.
        """
        self.user_facing_clock = user_facing_clock
        self.program_state = ApplicationInternalState("", "", {})
        self.chrome_state = ChromeInternalState("", "", "", {})
        self.current_state: InternalState | None = None
        self.prior_state: InternalState | None = None
        self.transition_from_program = TransitionFromProgramMachine(
            self.program_state)
        self.transition_from_chrome = TransitionFromChromeMachine(
            self.chrome_state)
        self.state_listeners = []
        self.logger = ConsoleLogger()

    def set_new_session(self, next_state: ProgramSessionData | ChromeSessionData):
        if self.current_state:
            prior_update_was_program = isinstance(
                self.current_state, ApplicationInternalState)
            if prior_update_was_program:
                updated_state = self.transition_from_program.compute_next_state(
                    next_state)
                # updated_overall_state = OverallState()
            else:
                updated_state = self.transition_from_chrome.compute_next_state(
                    next_state)
            self._conclude_session(self.current_state)
            self.prior_state = self.current_state
            self.current_state = updated_state
        else:
            # No current state yet, this is initialization:
            if isinstance(next_state, ProgramSessionData):
                is_chrome = window_is_chrome(next_state.window_title)
                updated_state = ApplicationInternalState(
                    next_state.window_title, is_chrome, next_state)
            else:
                updated_state = ChromeInternalState(
                    "Chrome", True, next_state.domain, next_state)
            self.current_state = updated_state

    def _conclude_session(self, state: InternalState):
        now = self.user_facing_clock.now()
        # Now - UTC
        # state.session.start_time - no tzinfo
        # FIXME: getting vals like 8h01m, 8h02m
        session_start = state.session.start_time

        duration = now - session_start

        # if not self.user_facing_clock.is_timezone_aware(now):
        #     raise TimezoneUnawareError("now")
        # elif not self.user_facing_clock.is_timezone_aware(session_start):
        #     raise TimezoneUnawareError("now")
        # elif not self.user_facing_clock.timezones_are_same(now, session_start):
        #     raise MismatchedTimezonesError()
        # else:
        #     print(now.tzinfo, now)
        #     print(session_start.tzinfo, session_start)
        #     self.logger.log_blue("[debug] none of those errors happened")

        # if duration > timedelta(hours=1):
        #     self.logger.log_red_multiple(
        #         "[critical - Concl Session] :: ", str(duration))
        #     raise SuspiciousDurationError("duration")
        # else:

        #     self.logger.log_blue("[debug] duration was ok: " + str(duration))

        state.session.duration = duration
        state.session.end_time = now

    def get_finished_state(self) -> InternalState | None:
        return self.prior_state

    def conclude_without_replacement(self):
        """For wrap up when the computer is powering off to avoid sessions left open"""
        if self.current_state is None:
            return  # Nothing to wrap up
        self._conclude_session(self.current_state)
        session_for_daos = self.current_state.session
        self.current_state = None  # Reset for power back on
        return session_for_daos


class TransitionFromProgramMachine:
    def __init__(self, current_state):
        if not isinstance(current_state, ApplicationInternalState):
            raise TypeError(
                "TransitionFromProgramMachine requires an ApplicationInternalState")

        self.current_state = current_state

    def compute_next_state(self, next_state: ProgramSessionData | ChromeSessionData) -> InternalState:
        if isinstance(next_state, ProgramSessionData):
            return self._change_to_new_program(next_state)
        else:
            return self._transit_to_chrome_state(next_state)

    def _change_to_new_program(self, next: ProgramSessionData) -> ApplicationInternalState:
        # TODO: If next state is the same program, return current state
        is_same_program = self.current_state.active_application == next.window_title
        if is_same_program:
            return self._stay_on_same_program()
        else:
            # Program A -> Program B, neither is Chrome
            # Create a new state that is on a different program
            is_chrome = False
            current_tab = None
            next_state = ApplicationInternalState(
                next.window_title, is_chrome, next)
            return next_state

    def _stay_on_same_program(self) -> ApplicationInternalState:
        return self.current_state  # No change needed

    def _transit_to_chrome_state(self, next: ChromeSessionData) -> ChromeInternalState:
        # FIXME: What to do with the case where, where, there is a new Chrome opening?
        # A new tab opens at the same time as Chrome opens.
        # FIXME: What to do with, case where, a tab was suspended in the bg
        # while user ran VSCode, now he goes back to Claude?
        next_state = ChromeInternalState(active_application="Chrome",
                                         is_chrome=True,
                                         current_tab=next.domain,
                                         session=next)
        return next_state


class TransitionFromChromeMachine:
    def __init__(self,  current_state):

        if not isinstance(current_state, ChromeInternalState):
            raise TypeError(
                "TransitionFromChromeMachine requires a ChromeInternalState")

        self.current_state = current_state

    def compute_next_state(self, next_state: ProgramSessionData | ChromeSessionData) -> InternalState:
        if isinstance(next_state, ProgramSessionData):
            return self._transit_to_program(next_state)
        else:
            return self._handle_change_tabs(next_state)

    def _transit_to_program(self, next_state: ProgramSessionData) -> InternalState:
        now_on_regular_app = not window_is_chrome(next_state.window_title)
        if now_on_regular_app:
            return self._change_to_new_program(next_state)
        else:
            return self._stay_on_chrome()  # Still on Chrome - Pass

    def _handle_change_tabs(self, next_state: ChromeSessionData) -> ChromeInternalState:
        on_different_tab = self.current_state.current_tab != next_state.domain
        if on_different_tab:
            return self._change_to_new_tab(next_state)
        else:
            return self._stay_on_current_tab()

    def _change_to_new_program(self, next: ProgramSessionData) -> ApplicationInternalState:
        # TODO: How to implement changing the program?
        # Create a new state that is a Program state
        is_chrome = False
        current_tab = None  # should it be whatever is open in chrome? if Chrome is open
        next_state = ApplicationInternalState(
            next.window_title, is_chrome, next)
        return next_state

    def _stay_on_chrome(self) -> ChromeInternalState:
        return self.current_state  # Explicitly stay the same

    def _change_to_new_tab(self, next: ChromeSessionData) -> ChromeInternalState:
        next_state = ChromeInternalState(active_application="Chrome",
                                         is_chrome=True,
                                         current_tab=next.domain,
                                         session=next)
        return next_state

    def _stay_on_current_tab(self) -> ChromeInternalState:
        # Chrome, currentDomain -> Chrome, currentDomain
        # "Skip over" this state change.
        return self.current_state  # Explicitly keep the same object as state
