from __future__ import annotations

from datetime import datetime, timedelta, timezone

from activitytracker.object.classes import (
    ChromeSession,
    CompletedChromeSession,
    CompletedProgramSession,
    ProgramSession,
)
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.copy_util import snapshot_obj_for_tests

from .session_polling import KeepAliveEngine, ThreadedEngineContainer
from .state_machine import StateMachine


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
        self.state_machine = StateMachine(user_facing_clock)
        self.sleep_detector = sleep_detector
        self.engine_class = engine_class
        # Threaded container must receive the pulse interval outside of here.
        # The engine is then set using the add and replace methods.
        self.current_pulse = threaded_container
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

    def notify_summary_dao(
        self, session: CompletedProgramSession | CompletedChromeSession | None
    ):
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
        # FIXME: When you alt tab BACK into Chrome, the session is "Google Chrome". But,
        # that's wrong! I don't want it to be Google Chrome. I want it to be Chrome's active tab.
        # FIXME: If you Play a youtube video, tab out, and then tab back into Chrome, but
        # don't do anything except watch the Youtube video, the time IS NOT RECORDED. It's
        # recorded as "Google Chrome".
        # Solution statement: Lodge whatever Chrome session is latest in a property.
        # When you alt tab back into Chrome, i.e. when the Session type is "Chrome",
        # restore the proper type using that latest type.
        # PROBLEM: But then how does it handle a situation where User has multiple Chrome windows?
        if isinstance(new_session, ProgramSession):
            self.logger.log_white("[Exe]", new_session.window_title)
        else:
            self.logger.log_white("[Tab]", new_session.domain)
        if new_session.video_info:
            self.logger.log_white("[Vid]", new_session.video_info)

        # TODO: Check in here, "Is this session the first one
        # since, like, 8 hours of inactivity?" via the StatusDao

        looks_like_sleep_occurred, time_before_lg_gap = (
            self.sleep_detector.detect_awakening_from_sleep()
        )
        print("sleep detection: ", looks_like_sleep_occurred, time_before_lg_gap)

        if looks_like_sleep_occurred:
            self.logger.log_yellow_multiple(
                "[warn] detect sleep results:", looks_like_sleep_occurred, time_before_lg_gap
            )
            self.flush_and_reset(time_before_lg_gap)

        self.notify_display_update(new_session)

        if self.state_machine.current_state:
            if self.current_pulse is None:
                raise ValueError("First loop failed in Activity Arbiter")

            # end_time & duration is set inside the ASM

            # FIXME: Should be concluded = self.machine.set_new(new_session)
            # TODO: There needs to be a way for a "still there?" signal to
            # come in from the client. Or does there?
            # "ServerOutOfSyncError" -> log info about how it came to be.
            # But also YAGNI? SO try it without polling first, until
            # you discover a problem.
            latest_status_write = self.sleep_detector.get_latest_write_time()
            if latest_status_write:
                # Problem statement: After sleeping the PC, the
                # So if the latest_status_write is more than ten sec ago,
                # it likely means this incoming session is from right after a sleep,
                # and so the duration of the outgoing session will include
                # the time the computer was asleep!
                suspicious_write_time = (
                    latest_status_write.dt < new_session.start_time - timedelta(minutes=2)
                )
                if suspicious_write_time:
                    time_since_latest_write = (
                        latest_status_write.dt - incoming_session_start.dt
                    ).total_seconds() / 60
                    self.logger.log_yellow(
                        f"[warn] latest status write was {time_since_latest_write:2f} min ago"
                    )
            self.state_machine.set_new_session(new_session)

            concluded_session = self.state_machine.get_concluded_session()
            self.notify_of_new_session(new_session)

            # self.current_pulse.stop()  # stop the old one from prev loop

            new_keep_alive_engine = self.engine_class(new_session, self.activity_recorder)

            self.current_pulse.replace_engine(new_keep_alive_engine)
            # print("Starting pulse in regular loop")
            # self.current_pulse.start()

            if self.state_machine.is_initialization_session(concluded_session):
                return  # It's just null state
            # -- Put outgoing state into the DAO
            self.notify_summary_dao(concluded_session)
        else:
            self.logger.log_white("in arbiter init")
            self.initialize_loop(new_session)

            self.notify_of_new_session(new_session)
            self.state_machine.set_new_session(new_session)

            new_keep_alive_engine = self.engine_class(new_session, self.activity_recorder)

            self.current_pulse.add_first_engine(new_keep_alive_engine)
            print("Starting pulse in init loop")

            self.current_pulse.start()

    def initialize_loop(self, first_session):
        """Exists so it's more testable"""
        pass

    def flush_and_reset(self, last_status_before_sleep):
        """Interrupts the current loop of transition_state to shut it down early."""
        # TODO: Want that the currently active session is closed at um, when?
        # I guess whenever the last status log before the large gap was.
        # TODO: And then, the whole thing should be reset so that it can go
        # into the else block again
        concluded_session = self.state_machine.conclude_without_replacement_at_time(
            last_status_before_sleep
        )
        self.current_pulse.stop()
        self.notify_summary_dao(concluded_session)

    def shutdown(self):
        """Concludes the current state/session without adding a new one"""
        if self.state_machine.current_state:
            concluded_session = self.state_machine.conclude_without_replacement()
            if concluded_session:
                self.notify_summary_dao(concluded_session)
