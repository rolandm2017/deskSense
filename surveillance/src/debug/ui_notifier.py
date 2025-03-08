from ..object.arbiter_classes import ApplicationInternalState, ChromeInternalState, InternalState
from ..object.classes import ProgramSessionData, ChromeSessionData


class UINotifier:
    def __init__(self, overlay):
        """
        Exists to keep the Overlay separate from the ActivityArbiter.

        It only handles UI updates for the debug overlay.
        """
        self.overlay = overlay

    def on_state_changed(self, session: InternalState):
        if isinstance(session, ProgramSessionData):
            display_text = session.window_title
            self.overlay.change_display_text(display_text, "lime")
        elif isinstance(session, ChromeSessionData):
            display_text = f"{session.domain}"
            # display_text = f"Chrome | {session.domain}"
            self.overlay.change_display_text(display_text, "#4285F4")
        else:
            print(type(session))
            raise TypeError("Type wasn't an expected SessionData")


def get_program_display_info(window_title):
    return {
        "text": window_title,
        "color": "lime"  # Could have a color map like the overlay
    }


def get_chrome_display_info(domain):
    return {
        "text": f"Chrome | {domain}",
        "color": "#4285F4"
    }


def get_display_info(state):
    if isinstance(state, ChromeInternalState):
        print(state.session)
        return get_chrome_display_info(state.session.domain)
    else:
        print(state.session)
        return get_program_display_info(state.session.window_title)
