from ..object.classes import ChromeSessionData, ProgramSessionData
from ..util.program_tools import window_is_chrome


class InternalState:
    def __init__(self, active_application, is_chrome, current_tab, session):
        self.active_application = active_application
        self.is_chrome = is_chrome
        self.current_tab = current_tab
        self.session = session

    def compute_next_state(self, next_state: ProgramSessionData | ChromeSessionData):
        raise NotImplementedError


class ApplicationInternalState(InternalState):
    def __init__(self, active_application, is_chrome, current_tab, session):
        super().__init__(active_application, is_chrome, current_tab, session)

    def compute_next_state(self, next_state: ProgramSessionData | ChromeSessionData):
        if isinstance(next_state, ProgramSessionData):
            return self.change_to_new_program(next_state)
        else:
            return self.transit_to_chrome_state(next_state)

    def change_to_new_program(self, next: ProgramSessionData):
        # TODO: If next state is the same program, return current state
        is_same_program = next.window_title == self.active_application
        if is_same_program:
            return self.stay_on_same_program()
        else:
            # Program A -> Program B, neither is Chrome
            # Create a new state that is on a different program
            is_chrome = False
            current_tab = None
            next_state = ApplicationInternalState(
                next.window_title, is_chrome, current_tab, next)
            return next_state

    def stay_on_same_program(self):
        return self  # No change needed

    def transit_to_chrome_state(self, next: ChromeSessionData):
        # FIXME: What to do with the case where, where, there is a new Chrome opening?
        # A new tab opens at the same time as Chrome opens.
        # FIXME: What to do with, case where, a tab was suspended in the bg
        # while user ran VSCode, now he goes back to Claude?
        next_state = ChromeInternalState(active_application="Chrome",
                                         is_chrome=True,
                                         current_tab=next.domain,
                                         session=next)
        return next_state


class ChromeInternalState(InternalState):
    def __init__(self, active_application, is_chrome, current_tab, session):
        super().__init__(active_application, is_chrome, current_tab, session)

    def compute_next_state(self, next_state: ProgramSessionData | ChromeSessionData):
        if isinstance(next_state, ProgramSessionData):
            return self.handle_change_to_program(next_state)
        else:
            return self.handle_change_tabs(next_state)

    def handle_change_to_program(self, next_state: ProgramSessionData):
        now_on_regular_app = not window_is_chrome(next_state.window_title)
        if now_on_regular_app:
            return self.change_to_new_program(next_state)
        else:
            return self.stay_on_chrome()  # Still on Chrome - Pass

    def handle_change_tabs(self, next_state: ChromeSessionData):
        on_different_tab = self.current_tab != next_state.domain
        if on_different_tab:
            self.change_to_new_tab(next_state)
        else:
            self.stay_on_current_tab()

    def change_to_new_program(self, next: ProgramSessionData):
        # TODO: How to implement changing the program?
        # Create a new state that is a Program state
        is_chrome = False
        current_tab = None  # should it be whatever is open in chrome? if Chrome is open
        next_state = ApplicationInternalState(
            next.window_title, is_chrome, current_tab, next)
        return next_state

    def stay_on_chrome(self):
        return self  # Explicitly stay the same

    def change_to_new_tab(self, next: ChromeSessionData):
        next_state = ChromeInternalState(active_application="Chrome",
                                         is_chrome=True,
                                         current_tab=next.domain,
                                         session=next)
        return next_state

    def stay_on_current_tab(self):
        # Chrome, currentDomain -> Chrome, currentDomain
        # "Skip over" this state change.
        return self  # Explicitly keep the same object as state
