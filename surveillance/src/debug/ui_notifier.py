from ..object.arbiter_classes import ApplicationInternalState, ChromeInternalState


class UINotifier:
    def __init__(self, overlay):
        """
        Exists to keep the Overlay separate from the ActivityArbiter.

        It only handles UI updates for the debug overlay.
        """
        self.overlay = overlay

    async def on_state_changed(self, new_state):
        if isinstance(new_state, ApplicationInternalState):
            display_text = new_state.session.window_title
            self.overlay.change_display_text(display_text, "lime")
        else:
            display_text = f"{new_state.session.domain}"
            self.overlay.change_display_text(display_text, "#4285F4")


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
