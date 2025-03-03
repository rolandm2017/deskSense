from datetime import datetime
from pathlib import Path

import time
import threading
from tracemalloc import start

from ..util.console_logger import ConsoleLogger
from ..config.definitions import productive_apps, productive_categories, productive_sites, unproductive_apps
from ..facade.program_facade import ProgramApiFacadeCore
from ..util.detect_os import OperatingSystemInfo
from ..util.end_program_routine import end_program_readout, pretend_report_event
from ..util.clock import SystemClock
from ..util.threaded_tracker import ThreadedTracker
from ..util.program_tools import separate_window_name_and_detail, is_expected_shape_else_throw, tab_is_a_productive_tab, contains_space_dash_space, window_is_chrome
from ..util.strings import no_space_dash_space
from ..object.classes import ProgramSessionData


# TODO: report programs that aren't in the apps list.

class ProgramTrackerCore:
    def __init__(self, clock, program_api_facade, window_change_handler, conclude_session_handler):
        """
        !!!!! IMPORTANT - READ THIS FIRST !!!!!

        This class has ONE job: Track the currently active program. That's it.

        CORRECT USAGE:
            - Monitor which program is currently in focus
            - Detect when user switches programs (alt-tab events)

        INCORRECT USAGE - DO NOT:
            - Track keyboard state (outside of the current session)
            - Monitor mouse position/clicks
            - Read browser tab contents
            - Add any other tracking functionality outside of, "What is the current program?"

        If you find yourself adding any of the above, stop and rethink it!
        Create a separate class instead.
        """
        self.system_clock = clock
        self.program_facade: ProgramApiFacadeCore = program_api_facade
        self.window_change_handler = window_change_handler
        self.conclude_session_handler = conclude_session_handler
        # self.chrome_event_update = chrome_event_update

        # FIXME: why is there three "productive categories" fields?
        self.productive_apps = productive_apps
        self.unproductive = unproductive_apps
        self.productive_categories = productive_categories
        self.productive_sites = productive_sites

        self.current_is_chrome = False

        self.current_session: ProgramSessionData | None = None

        self.console_logger = ConsoleLogger()

    def run_tracking_loop(self):
        for window_change in self.program_facade.listen_for_window_changes():
            is_expected_shape_else_throw(window_change)
            # TODO: If Chrome is the new Active window, mark chrome active
            # TODO: If chrome is the CURRENT active window, and chrome is not active now, mark inactive

            on_a_different_window = self.current_session and window_change[
                "window_title"] != self.current_session.window_title
            if on_a_different_window and self.is_initialized():
                if self.current_session is None:
                    raise ValueError("Current session was None")

                current_time: datetime = self.system_clock.now()  # once per loop
                self.conclude_session(current_time)
                # when a window closes, call that with "conclude_session_handler()" to maintain other flows
                self.apply_handlers(self.current_session)
                new_session = self.start_new_session(
                    window_change, current_time)
                self.current_session = new_session
                # report window change immediately via "window_change_handler()"
                self.window_change_handler(new_session)

            # initialize
            if self.is_uninitialized():
                current_time = self.system_clock.now()
                new_session = self.start_new_session(
                    window_change, current_time)
                self.current_session = new_session
                self.window_change_handler(new_session)

    def is_uninitialized(self):
        return self.current_session is None

    def is_initialized(self):
        return not self.current_session is None
    # def is_initialization_session(self, session):
    #     if (session.window_title == "" and
    #         session.detail == "" and
    #             session.start_time is None):
    #         return True
    #     return False

    def start_new_session(self, window_change_dict, start_time):
        new_session = ProgramSessionData()
        if contains_space_dash_space(window_change_dict["window_title"]):
            detail, window = separate_window_name_and_detail(
                window_change_dict["window_title"])
            new_session.window_title = window
            new_session.detail = detail
        else:
            new_session.window_title = window_change_dict["window_title"]
            new_session.detail = no_space_dash_space
        new_session.start_time = start_time
        # end_time, duration, productive not set yet
        return new_session

    def conclude_session(self, end_time: datetime):
        if self.current_session is None:
            raise ValueError("Current session was None")
        # end_time = self.system_clock.now()
        start_time: datetime | None = self.current_session.start_time
        initializing = start_time is None
        if initializing:
            start_time = end_time  # whatever
        duration = end_time - start_time
        self.current_session.end_time = end_time
        self.current_session.duration = duration

    def report_missing_program(self, title):
        """For when the program isn't found in the productive apps list"""
        self.console_logger.log_yellow(title)  # temp

    def apply_handlers(self, session: ProgramSessionData):
        if not isinstance(session, ProgramSessionData):
            self.console_logger.log_yellow_multiple("[DEBUG]", session)
            raise ValueError("Was not a dict")
        #  {'os': 'Ubuntu', 'pid': 70442, 'process_name': 'pgadmin4', 'window_title': 'Alt-tab window'}
        # start_time, end_time, duration, window, productive
        if isinstance(self.conclude_session_handler, list):
            for handler in self.conclude_session_handler:
                handler(session)  # emit an event
        else:
            self.conclude_session_handler(session)  # is a single func

    def stop(self):
        pass  # might need later


if __name__ == "__main__":
    os_type = OperatingSystemInfo()
    program_api_facade = ProgramApiFacadeCore(os_type)

    # folder = Path("/tmp")

    clock = SystemClock()

    def placeholder_handler():
        return True

    try:

        tracker = ProgramTrackerCore(clock, program_api_facade, [
                                     end_program_readout, pretend_report_event], placeholder_handler)
        thread_handler = ThreadedTracker(tracker)
        thread_handler.start()
        # Add a way to keep the main thread alive
        while True:
            time.sleep(0.3)
    except KeyboardInterrupt:
        thread_handler.stop()
        # Give the thread time to clean up
        time.sleep(0.3)
