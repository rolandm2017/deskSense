from __future__ import annotations
from datetime import datetime, timedelta, timezone
import copy

from surveillance.src.config.definitions import power_on_off_debug_file

from surveillance.src.object.classes import ChromeSession, ProgramSession, CompletedChromeSession, CompletedProgramSession

from .activity_state_machine import ActivityStateMachine
from .session_heartbeat import KeepAliveEngine, ThreadedEngineContainer
from surveillance.src.util.console_logger import ConsoleLogger
from surveillance.src.util.copy_util import snapshot_obj_for_tests


class ActivityArbiter:
    def __init__(self, user_facing_clock, threaded_container,
                    engine_class=KeepAliveEngine):
        """
        This class exists to prevent the Chrome Service from doing ANYTHING but reporting which tab is active.

        This class exists to prevent the Program Tracker from doing ANYTHING except reporting the active program.

        This way, the Chrome Service doesn't need to know if Chrome is active.
        i.e. "chrome_open_close_handler" before e22d5badb15

        This way, the Program Tracker doesn't need to track if
        the current program is Chrome & do such and such if it is or isn't.
        i.e. "chrome_event_update" and "self.current_is_chrome" before e22d5badb15
        """
        self.state_machine = ActivityStateMachine(user_facing_clock)
        self.engine_class = engine_class
        # Threaded container must receive the pulse interval outside of here.
        # The engine is then set using the add and replace methods.
        self.current_heartbeat = threaded_container
        self.ui_update_listener = None
        self.activity_recorder = None
        self.logger = ConsoleLogger()

    def add_ui_listener(self, listener):
        self.ui_update_listener = listener

    def notify_display_update(self, state):
        if self.ui_update_listener:
            self.ui_update_listener(state)

    def add_recorder_listener(self, listener):
        if hasattr(listener, "on_state_changed"):
            self.activity_recorder = listener
        else:
            raise AttributeError("Listener method was missing")

    def notify_summary_dao(self, session: CompletedProgramSession | CompletedChromeSession | None):
        if self.activity_recorder:
            self.activity_recorder.on_state_changed(session)

    def notify_of_new_session(self, session: ProgramSession | ChromeSession):
        if self.activity_recorder:
            # Prevent mutations from ruining test data
            session_copy = snapshot_obj_for_tests(session)
            self.activity_recorder.on_new_session(session_copy)

    def set_program_state(self, event: ProgramSession):
        self.transition_state(event)

    def set_tab_state(self, tab: ChromeSession):
        self.transition_state(tab)

    def transition_state(self, new_session: ChromeSession | ProgramSession):
        """
        If newly_active = Chrome, start a session for the current tab.
        When Chrome is closed, end the session for the current tab.

        When a program is opened, start a session for the program. And vice versa when it closes.
        """
        if isinstance(new_session, ProgramSession):
            self.logger.log_white("[Arb]", new_session.window_title)
        else:
            self.logger.log_white("[Tab]", new_session.domain)
        assert not isinstance(
            new_session, dict), "Found an empty dictionary as session"
        self.notify_display_update(new_session)
        if self.state_machine.current_state:
            if self.current_heartbeat is None:
                raise ValueError("First loop failed in Activity Arbiter")

            # end_time & duration is set inside the ASM

            self.state_machine.set_new_session(new_session)

            concluded_session = self.state_machine.get_concluded_session()

            # ### Start the first window
            self.notify_of_new_session(new_session)

            self.current_heartbeat.stop()  # stop the old one from prev loop

            new_keep_alive_engine = self.engine_class(
                new_session, self.activity_recorder)
            
            self.current_heartbeat.replace_engine(new_keep_alive_engine)

            self.current_heartbeat.start()

            if self.state_machine.is_initialization_session(concluded_session):
                return  # It's just null state
            # -- Put outgoing state into the DAO
            self.notify_summary_dao(concluded_session)
        else:
            self.logger.log_white("in arbiter init")

            self.notify_of_new_session(new_session)
            self.state_machine.set_new_session(new_session)
            
            new_keep_alive_engine = self.engine_class(
                new_session, self.activity_recorder)
            
            self.current_heartbeat.add_first_engine(new_keep_alive_engine)

            self.current_heartbeat.start()

    def shutdown(self):
        """Concludes the current state/session without adding a new one"""
        if self.state_machine.current_state:
            concluded_session = self.state_machine.conclude_without_replacement()
            if concluded_session:
                self.notify_summary_dao(concluded_session)
            with open(power_on_off_debug_file, "a") as f:
                f.write("Shutdown Activity Arbiter\n")
