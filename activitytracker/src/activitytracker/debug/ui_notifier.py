from activitytracker.object.arbiter_classes import (
    ApplicationInternalState,
    ChromeInternalState,
    InternalState,
)
from activitytracker.object.classes import ProgramSession, ChromeSession


class UINotifier:
    def __init__(self, overlay):
        """
        Exists to keep the Overlay separate from the ActivityArbiter.

        It only handles UI updates for the debug overlay.
        """
        self.overlay = overlay

    def on_state_changed(self, session: InternalState | ProgramSession | ChromeSession):
        if isinstance(session, ProgramSession):
            display_text = session.window_title
            self.overlay.change_display_text(display_text, "lime")
        elif isinstance(session, ChromeSession):
            display_text = f"{session.domain}"
            # display_text = f"Chrome | {session.domain}"
            self.overlay.change_display_text(display_text, "#4285F4")
        elif isinstance(session, ApplicationInternalState):
            attached = session.session
            display_text = attached.window_title
            self.overlay.change_display_text(display_text, "lime")
        elif isinstance(session, ChromeInternalState):
            attached = session.session
            display_text = f"{attached.domain}"
            self.overlay.change_display_text(display_text, "#4285F4")
        else:
            print(type(session))
            raise TypeError("Type wasn't an expected Session or State")


def get_program_display_info(window_title):
    return {"text": window_title, "color": "lime"}  # Could have a color map like the overlay


def get_chrome_display_info(domain):
    return {"text": f"Chrome | {domain}", "color": "#4285F4"}
