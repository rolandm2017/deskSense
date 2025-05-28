import time
from datetime import datetime

from curses import window

from activitytracker.config.definitions import no_space_dash_space
from activitytracker.facade.program_facade_base import ProgramFacadeInterface
from activitytracker.object.classes import ProgramSession
from activitytracker.object.enums import PlayerState
from activitytracker.object.video_classes import VlcInfo
from activitytracker.util.clock import SystemClock
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.detect_os import OperatingSystemInfo
from activitytracker.util.eventful_threaded_tracker import EventBasedThreadedTracker
from activitytracker.util.program_tools import (
    contains_space_dash_space,
    separate_window_name_and_detail,
)
from activitytracker.util.sync_periodic_task import SyncPeriodicTask
from activitytracker.util.time_wrappers import UserLocalTime

from .vlc_player_query import VlcMediaPlayerTracker, get_vlc_status

# TODO: report programs that aren't in the apps list.


class ProgramTrackerCore:
    def __init__(
        self, user_facing_clock, program_api_facade, window_change_handler, handle_chrome
    ):
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
        self.handle_chrome = handle_chrome

        self.vlc_tracker = VlcMediaPlayerTracker()

        self.vlc_poller = SyncPeriodicTask(self.update_vlc_status, interval_in_sec=0.5)
        print(f"[init] vlc_poller created: {self.vlc_poller} (id: {id(self.vlc_poller)})")
        print(f"[init] self object id: {id(self)}")
        self.vlc_window = None

        self.latest_vlc_state = VlcInfo(
            "Initialize", "Init", "Init", player_state=PlayerState.PAUSED
        )

        self.current_session: ProgramSession | None = None

        self.console_logger = ConsoleLogger()

    def run_tracking_loop(self):
        print("Starting pure event-based window tracking...")
        # print(f"[DEBUG] Starting run_tracking_loop, vlc_poller: {self.vlc_poller}")
        # print(f"[DEBUG] self object id in run_tracking_loop: {id(self)}")

        for window_change in self.program_facade.listen_for_window_changes():

            # if self.vlc_is_active:
            # self.console_logger.log_white("\n\nINFO:", window_change)
            if self.window_is_vlc(window_change):
                self.vlc_window = window_change
                self.console_logger.log_white("was VLC!")

                self.start_vlc_polling()
            else:
                self.stop_vlc_polling()
                # self.console_logger.log_white("WAS NOT VLC!")
                # FIXME: "Running Server (WindowsTerminal.exe)" -> Terminal (Terminal)
                on_a_different_window_now = (
                    self.current_session
                    and window_change["window_title"] != self.current_session.window_title
                )
                if on_a_different_window_now and self.is_initialized():
                    if self.current_session is None:
                        raise ValueError("Current session was None")

                    current_time: UserLocalTime = (
                        self.user_facing_clock.now()
                    )  # once per loop

                    new_session = self.start_new_session(window_change, current_time)
                    self.current_session = new_session
                    # FILTER HERE: Only report the event if it's NOT Chrome
                    # https://claude.ai/chat/ede0b004-79ff-4b42-b191-40e8d3f91bf4
                    if self.window_is_chrome(window_change):
                        # Do not report Chrome, because Chrome will do its own reporting.
                        # Note that if you try to get out of this via early return, the
                        # code breaks. If you try to get out of it via "continue,"
                        # the code breaks.
                        # self.console_logger.log_white(
                        #     "Chrome session ignored - not forwarded to external handler"
                        # )
                        self.handle_chrome(new_session)
                    else:
                        self.window_change_handler(new_session)

                # initialize
                if self.is_uninitialized():
                    current_time: UserLocalTime = self.user_facing_clock.now()
                    # capture_program_data_for_tests(window_change, current_time)
                    new_session = self.start_new_session(window_change, current_time)
                    self.current_session = new_session
                    if self.window_is_chrome(window_change):
                        # self.console_logger.log_white(
                        #     "Chrome session ignored - not forwarded to external handler"
                        # )
                        self.handle_chrome(new_session)
                    else:
                        self.window_change_handler(new_session)

                    # self.window_change_handler(new_session)

    def vlc_media_changed(self, vlc_info_update: VlcInfo):
        """Compares to the current VLC session using custom __eq__"""
        return self.latest_vlc_state != vlc_info_update

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

    def start_vlc_polling(self):
        self.console_logger.log_yellow("Starting VLC polling")
        # print(f"[DEBUG] start_vlc_polling called, vlc_poller: {self.vlc_poller}")
        # print(f"[DEBUG] vlc_poller type: {type(self.vlc_poller)}")
        # print(f"[DEBUG] self object id in start_vlc_polling: {id(self)}")

        self.vlc_poller.start()

    def update_vlc_status(self):
        vlc_state = self.vlc_tracker.get_updated_vlc_status()

        if self.vlc_media_changed(vlc_state):
            current_time: UserLocalTime = self.user_facing_clock.now()
            updated_vlc_session = self.start_new_video_session(
                self.vlc_window, current_time, vlc_state
            )
            self.console_logger.log_yellow(
                "New VLC State: "
                + updated_vlc_session.video_info.file  # type: ignore
                + " :: "
                + updated_vlc_session.video_info.player_state.value  # type: ignore
            )
            self.window_change_handler(updated_vlc_session)
            self.current_session = updated_vlc_session

        self.latest_vlc_state = vlc_state

    def stop_vlc_polling(self):
        if self.vlc_poller:
            self.vlc_poller.stop()

    def window_is_vlc(self, window):
        current_os = "Linux"
        if current_os == "Linux":
            linux_name_for_vlc = "vlc"
            return window["process_name"] == linux_name_for_vlc
        else:
            # TODO: Find out what the name is
            windows_name_for_vlc = "TODO"
            return window["process_name"] == windows_name_for_vlc

    def window_is_chrome(self, window):
        current_os = "Linux"
        if current_os == "Linux":
            linux_name_for_chrome = "chrome"
            return window["process_name"] == linux_name_for_chrome
        else:
            # TODO: Find out what the name is
            windows_name_for_chrome = "TODO"
            return window["process_name"] == windows_name_for_chrome


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

        tracker = ProgramTrackerCore(clock, program_api_facade, ["", ""], None)
        thread_handler = EventBasedThreadedTracker(tracker)
        thread_handler.start()
        # Add a way to keep the main thread alive
        while True:
            time.sleep(0.3)
    except KeyboardInterrupt:
        thread_handler.stop()
        # Give the thread time to clean up
        time.sleep(0.3)
