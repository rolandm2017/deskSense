from curses import window
import time
from datetime import datetime

from surveillance.src.config.definitions import (
    no_space_dash_space,
    productive_apps,
    productive_categories,
    productive_sites,
    unproductive_apps,
)
from surveillance.src.facade.program_facade_base import ProgramFacadeInterface
from surveillance.src.object.classes import ProgramSession
from surveillance.src.util.clock import SystemClock
from surveillance.src.util.console_logger import ConsoleLogger
from surveillance.src.util.detect_os import OperatingSystemInfo
from surveillance.src.util.program_tools import (
    contains_space_dash_space,
    separate_window_name_and_detail,
)
from surveillance.src.util.threaded_tracker import ThreadedTracker
from surveillance.src.util.time_wrappers import UserLocalTime

# TODO: report programs that aren't in the apps list.


class ProgramTrackerCore:
    def __init__(self, user_facing_clock, program_api_facade, window_change_handler):
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
        self.user_facing_clock = user_facing_clock
        self.program_facade: ProgramFacadeInterface = program_api_facade
        self.window_change_handler = window_change_handler
        # self.chrome_event_update = chrome_event_update

        self.current_is_chrome = False

        self.current_session: ProgramSession | None = None

        self.console_logger = ConsoleLogger()

    def run_tracking_loop(self):
        for window_change in self.program_facade.listen_for_window_changes():
            # is_expected_shape_else_throw(window_change)
            # FIXME: "Running Server (WindowsTerminal.exe)" -> Terminal (Terminal)
            on_a_different_window_now = self.current_session and window_change[
                "window_title"] != self.current_session.window_title
            if on_a_different_window_now and self.is_initialized():
                if self.current_session is None:
                    raise ValueError("Current session was None")

                current_time: datetime = self.user_facing_clock.now()  # once per loop

                new_session = self.start_new_session(
                    window_change, current_time)
                self.current_session = new_session
                # report window change immediately via "window_change_handler()"
                self.window_change_handler(new_session)

            # initialize
            if self.is_uninitialized():
                current_time = self.user_facing_clock.now()
                # capture_program_data_for_tests(window_change, current_time)
                new_session = self.start_new_session(
                    window_change, current_time)
                self.current_session = new_session
                self.window_change_handler(new_session)

    def is_uninitialized(self):
        return self.current_session is None

    def is_initialized(self):
        return not self.current_session is None

    def start_new_session(self, window_change_dict, start_time) -> ProgramSession:
        if contains_space_dash_space(window_change_dict["window_title"]):
            detail, window_title = separate_window_name_and_detail(
                window_change_dict["window_title"])
        else:
            window_title = window_change_dict["window_title"]
            detail = no_space_dash_space
        new_session = ProgramSession(window_change_dict["exe_path"],
                                     window_change_dict["process_name"],
                                     window_title,
                                     detail,
                                     UserLocalTime(start_time))
        # end_time, duration, productive not set yet
        return new_session

    def report_missing_program(self, title):
        """For when the program isn't found in the productive apps list"""
        self.console_logger.log_yellow(title)  # temp

    def stop(self):
        pass


if __name__ == "__main__":
    os_type = OperatingSystemInfo()

    def choose_program_facade(os):
        if os.is_windows:
            from surveillance.src.facade.program_facade_windows import (
                WindowsProgramFacadeCore,
            )
            return WindowsProgramFacadeCore()
        else:
            from surveillance.src.facade.program_facade_ubuntu import (
                UbuntuProgramFacadeCore,
            )
            return UbuntuProgramFacadeCore()

    program_api_facade = choose_program_facade(os_type)

    # folder = Path("/tmp")

    clock = SystemClock()

    try:

        tracker = ProgramTrackerCore(clock, program_api_facade, [
                                     "", ""])
        thread_handler = ThreadedTracker(tracker)
        thread_handler.start()
        # Add a way to keep the main thread alive
        while True:
            time.sleep(0.3)
    except KeyboardInterrupt:
        thread_handler.stop()
        # Give the thread time to clean up
        time.sleep(0.3)
