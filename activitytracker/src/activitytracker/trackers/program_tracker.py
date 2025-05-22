from curses import window

import time
from datetime import datetime

from activitytracker.config.definitions import no_space_dash_space
from activitytracker.facade.program_facade_base import ProgramFacadeInterface
from activitytracker.object.classes import ProgramSession
from activitytracker.object.video_classes import VlcInfo
from activitytracker.util.clock import SystemClock
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.detect_os import OperatingSystemInfo
from activitytracker.util.program_tools import (
    contains_space_dash_space,
    separate_window_name_and_detail,
)
from activitytracker.util.threaded_tracker import ThreadedTracker
from activitytracker.util.time_wrappers import UserLocalTime

from .vlc_player_query import get_vlc_status

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
            # TODO: Wager I can delete self.current_session & related code
            on_a_different_window_now = (
                self.current_session
                and window_change["window_title"] != self.current_session.window_title
            )
            if on_a_different_window_now and self.is_initialized():
                if self.current_session is None:
                    raise ValueError("Current session was None")

                current_time: UserLocalTime = self.user_facing_clock.now()  # once per loop

                is_vlc = self.window_is_vlc(window_change)
                if is_vlc:
                    video_details = self.ask_vlc_player_for_info()
                    new_session = self.start_new_video_session(
                        window_change, current_time, video_details
                    )
                else:
                    new_session = self.start_new_session(window_change, current_time)
                self.current_session = new_session
                # report window change immediately via "window_change_handler()"
                self.console_logger.log_yellow("New program: " + new_session.process_name)
                self.window_change_handler(new_session)

            # initialize
            if self.is_uninitialized():
                current_time: UserLocalTime = self.user_facing_clock.now()
                # capture_program_data_for_tests(window_change, current_time)
                new_session = self.start_new_session(window_change, current_time)
                self.current_session = new_session
                self.window_change_handler(new_session)

    def ask_vlc_player_for_info(self) -> VlcInfo | None:
        return get_vlc_status()

    def is_uninitialized(self):
        return self.current_session is None

    def is_initialized(self):
        return not self.current_session is None

    def start_new_session(
        self, window_change_dict, start_time: UserLocalTime
    ) -> ProgramSession:
        detail, window_title = self.prepare_window_name_and_detail(window_change_dict)
        new_session = ProgramSession(
            window_change_dict["exe_path"],
            window_change_dict["process_name"],
            window_title,
            detail,
            start_time,
        )
        # end_time, duration, productive not set yet
        return new_session

    def start_new_video_session(self, window_dict, start_time, video_info):
        detail, window_title = self.prepare_window_name_and_detail(window_dict)
        new_session = ProgramSession(
            window_dict["exe_path"],
            window_dict["process_name"],
            window_title,
            detail,
            start_time,
            video_info,
        )
        # end_time, duration, productive not set yet
        return new_session

    def prepare_window_name_and_detail(self, window_dict):
        if contains_space_dash_space(window_dict["window_title"]):
            detail, window_title = separate_window_name_and_detail(
                window_dict["window_title"]
            )
        else:
            window_title = window_dict["window_title"]
            detail = no_space_dash_space
        return detail, window_title

    def window_is_vlc(self, window):
        current_os = "Linux"
        if current_os == "Linux":
            linux_name_for_vlc = "vlc"
            return window["process_name"] == linux_name_for_vlc
        else:
            # TODO: Find out what the name is
            windows_name_for_vlc = "Bar"
            return window["process_name"] == windows_name_for_vlc


if __name__ == "__main__":
    os_type = OperatingSystemInfo()

    def choose_program_facade(os):
        if os.is_windows:
            from activitytracker.facade.program_facade_windows import (
                WindowsProgramFacadeCore,
            )

            return WindowsProgramFacadeCore()
        else:
            from activitytracker.facade.program_facade_ubuntu import (
                UbuntuProgramFacadeCore,
            )

            return UbuntuProgramFacadeCore()

    program_api_facade = choose_program_facade(os_type)

    # folder = Path("/tmp")

    clock = SystemClock()

    try:

        tracker = ProgramTrackerCore(clock, program_api_facade, ["", ""])
        thread_handler = ThreadedTracker(tracker)
        thread_handler.start()
        # Add a way to keep the main thread alive
        while True:
            time.sleep(0.3)
    except KeyboardInterrupt:
        thread_handler.stop()
        # Give the thread time to clean up
        time.sleep(0.3)
