from __future__ import annotations

from activitytracker.object.classes import (
    ChromeSession,
    CompletedChromeSession,
    CompletedProgramSession,
    ProgramSession,
)
from activitytracker.util.copy_util import snapshot_obj_for_tests


class ActivityNotifier:
    """Owns UI and recorder listener mechanics.

    The arbiter decides *when* to notify; this class handles registration,
    listener-shape checks, and per-event dispatch.
    """

    def __init__(self):
        self._ui_listener = None
        self._recorder = None

    def add_ui_listener(self, listener):
        self._ui_listener = listener

    def add_recorder_listener(self, listener):
        if not hasattr(listener, "on_state_changed"):
            raise AttributeError("Listener method was missing")
        self._recorder = listener

    @property
    def recorder(self):
        return self._recorder

    def notify_display_update(self, session: ProgramSession | ChromeSession) -> None:
        if self._ui_listener:
            self._ui_listener(session)

    def notify_new_session(self, session: ProgramSession | ChromeSession) -> None:
        if self._recorder:
            session_copy = snapshot_obj_for_tests(session)
            self._recorder.on_new_session(session_copy)

    def notify_completed_session(
        self,
        session: CompletedProgramSession | CompletedChromeSession | None,
    ) -> None:
        if self._recorder:
            self._recorder.on_state_changed(session)
