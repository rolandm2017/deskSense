from ..object.classes import ChromeSessionData, ProgramSessionData
from ..util.program_tools import window_is_chrome


class InternalState:
    def __init__(self, active_application, is_chrome, session):
        self.active_application = active_application
        self.is_chrome = is_chrome
        self.session = session


class ApplicationInternalState(InternalState):
    def __init__(self, active_application, is_chrome, session):
        # NOTE: is_chrome is needed to indicate when the application, well, is on Chrome!
        # And therefore should check what the chrome state says about the current tab.
        super().__init__(active_application, is_chrome, session)


class ChromeInternalState(InternalState):
    def __init__(self, active_application, is_chrome, current_tab, session):
        # TODO: Remove active application & is_chrome from this. It doesn't need it
        super().__init__(active_application, is_chrome, session)
        self.current_tab = current_tab
