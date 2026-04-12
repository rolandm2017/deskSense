from __future__ import annotations

from dataclasses import dataclass

from activitytracker.object.classes import (
    ChromeSession,
    CompletedChromeSession,
    CompletedProgramSession,
    ProgramSession,
)
from activitytracker.util.console_logger import ConsoleLogger

from .activity_notifier import ActivityNotifier
from .pulse_controller import PulseController
from .session_polling import KeepAliveEngine, ThreadedEngineContainer
from .sleep_gap_handler import SleepGapHandler
from .active_session_state import ActiveSessionState


@dataclass
class TransitionOutcome:
    new_session: ProgramSession | ChromeSession
    concluded_session: CompletedProgramSession | CompletedChromeSession | None
    was_initialization: bool


class ActivityArbiter:
    def __init__(
        self,
        user_facing_clock,
        sleep_detector,
        threaded_container: ThreadedEngineContainer,
        engine_class=KeepAliveEngine,
    ):
        """
        This class exists to prevent the Chrome Service from doing ANYTHING but reporting which tab is active.

        This class exists to prevent the Program Tracker from doing ANYTHING except reporting the active program.

        This way, the Chrome Service doesn't need to know if Chrome is active.
        i.e. "chrome_open_close_handler" before e22d5badb15

        This way, the Program Tracker doesn't need to track if
        the current program is Chrome & do such and such if it is or isn't.
        i.e. "chrome_event_update" and "self.current_is_chrome" before e22d5badb15
        """
        self.active_session_state = ActiveSessionState(user_facing_clock)
        self.sleep_detector = sleep_detector
        self.logger = ConsoleLogger()
        self.notifier = ActivityNotifier()
        self.pulse_controller = PulseController(threaded_container, engine_class)
        self.sleep_gap_handler = SleepGapHandler(sleep_detector, self.logger)

    def add_ui_listener(self, listener):
        self.notifier.add_ui_listener(listener)

    def add_recorder_listener(self, listener):
        self.notifier.add_recorder_listener(listener)
        self.pulse_controller.set_recorder(listener)

    @property
    def activity_recorder(self):
        return self.notifier.recorder

    def set_program_state(self, event: ProgramSession):
        self.transition_state(event)

    def set_tab_state(self, tab: ChromeSession):
        self.transition_state(tab)

    def _advance_state(
        self, new_session: ChromeSession | ProgramSession
    ) -> TransitionOutcome:
        was_initialization = self.active_session_state.current_state is None
        concluded = self.active_session_state.set_new_session(new_session)
        return TransitionOutcome(new_session, concluded, was_initialization)

    def transition_state(self, new_session: ChromeSession | ProgramSession):
        """
        If newly_active = Chrome, start a session for the current tab.
        When Chrome is closed, end the session for the current tab.

        When a program is opened, start a session for the program. And vice versa when it closes.
        """
        if isinstance(new_session, ProgramSession):
            self.logger.log_white("[Exe]", new_session.window_title)
        else:
            self.logger.log_white("[Tab]", new_session.domain)
            if new_session.video_info:
                self.logger.log_white("[vid]", new_session.video_info)
        assert not isinstance(new_session, dict), "Found an empty dictionary as session"

        sleep_decision = self.sleep_gap_handler.inspect_before_transition(new_session)
        if sleep_decision.should_flush:
            self.flush_and_reset(sleep_decision.end_time)

        self.notifier.notify_display_update(new_session)

        outcome = self._advance_state(new_session)

        if not outcome.was_initialization:
            self.notifier.notify_new_session(new_session)
            self.pulse_controller.replace_with(new_session)

            if (
                outcome.concluded_session is None
                or self.active_session_state.is_initialization_session(outcome.concluded_session)
            ):
                return  # It's just null state
            self.notifier.notify_completed_session(outcome.concluded_session)
        else:
            self.logger.log_white("in arbiter init")
            self.initialize_loop(new_session)
            self.notifier.notify_new_session(new_session)
            print("Starting pulse in init loop")
            self.pulse_controller.start_first(new_session)

    def initialize_loop(self, first_session):
        """Exists so it's more testable"""
        pass

    def flush_and_reset(self, last_status_before_sleep):
        """Interrupts the current loop of transition_state to shut it down early."""
        concluded_session = self.active_session_state.conclude_without_replacement_at_time(
            last_status_before_sleep
        )
        self.pulse_controller.stop()
        self.notifier.notify_completed_session(concluded_session)

    def shutdown(self):
        """Concludes the current state/session without adding a new one"""
        if self.active_session_state.current_state:
            concluded_session = self.active_session_state.conclude_without_replacement()
            if concluded_session:
                self.notifier.notify_completed_session(concluded_session)
