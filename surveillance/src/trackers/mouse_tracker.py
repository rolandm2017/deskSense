# src/trackers/mouse_tracker.py
from enum import Enum, auto

import asyncio

from pathlib import Path
import threading
from threading import Thread
import time

from ..util.clock import Clock
from ..util.detect_os import OperatingSystemInfo
from ..util.end_program_routine import end_program_readout, pretend_report_event
from ..util.threaded_tracker import ThreadedTracker
from ..object.enums import MouseEvent
from ..object.classes import MouseMoveWindow
from ..console_logger import ConsoleLogger
from ..facade.mouse_facade import UbuntuMouseApiFacadeCore, WindowsMouseApiFacade


class MouseTrackerCore:
    def __init__(self, clock, mouse_api_facade, event_handlers, end_program_routine=None):
        self.clock = clock
        self.mouse_facade: UbuntuMouseApiFacadeCore = mouse_api_facade
        self.event_handlers = event_handlers

        self.end_program_func = end_program_routine
        self.environment = OperatingSystemInfo()

        self.movement_start_time = None
        self.last_position = None
        self.is_moving = False

        self.console_logger = ConsoleLogger()

        self.session_data = []
        self.mouse_movement_window = "Closed"

    def get_mouse_position(self):
        coords = self.mouse_facade.get_position_coords()
        # print(coords, '56ru')
        coords.timestamp = self.clock.now()
        return coords

    def position_is_same_as_before(self, new_position):
        return self.last_position.x == new_position.x and self.last_position.y == new_position.y

    def mouse_is_moving(self, coords):
        previous = self.last_position
        is_still_moving = previous.x != coords.x or previous.y != coords.y
        return is_still_moving

    def start_tracking_movement(self, latest_result):
        # self.console_logger.log_green("[LOG] Start movement window")
        self.is_moving = True
        self.last_position = latest_result
        self.movement_start_time = self.clock.now()

    def keep_window_open_and_update(self, latest_reading):
        self.last_position = latest_reading  # I think this is enough

    def close_and_retrieve_window(self, latest_result) -> MouseMoveWindow:
        """Handle the mouse stopping."""
        # self.console_logger.log_green("[LOG] End movement window")
        self.is_moving = False
        return MouseMoveWindow(self.movement_start_time, latest_result.timestamp)

    def run_tracking_loop(self):
        latest_result = self.get_mouse_position()
        if self.is_moving:
            has_stopped = self.position_is_same_as_before(latest_result)
            if has_stopped:
                window: MouseMoveWindow = self.close_and_retrieve_window(
                    latest_result)
                self.session_data.append(window)
                self.apply_handlers(window)
                self.reset()
            else:
                self.keep_window_open_and_update(latest_result)
        else:
            if self.last_position is None:
                self.last_position = latest_result
            if self.mouse_is_moving(latest_result):
                self.start_tracking_movement(latest_result)

    def reset(self):
        self.movement_start_time = None

    def handle_mouse_stop(self, latest_result):
        return self.close_and_retrieve_window(latest_result)  # Alias

    def apply_handlers(self, content: MouseMoveWindow):
        if isinstance(self.event_handlers, list):
            for handler in self.event_handlers:
                handler(content)  # emit an event
        else:
            self.event_handlers(content)  # is a single func

    def gather_session(self):
        current = self.session_data
        return current
        # TODO: make currently open mouse movements not be reported, move them to the next interval
        # self.session_data = self.preserve_open_events(current)
        # return current

    def preserve_open_events(self, current_batch):
        # FIXME: convert to accept .start_time, .end_time events. is this needed?
        # There can be one or zero open events, not 2.
        to_preserve = []
        if current_batch:
            if current_batch[-1]["event_type"] == MouseEvent.START:
                to_preserve.append(current_batch[-1])
        return to_preserve

    def stop(self):
        if self.end_program_func:
            self.end_program_func(None)


def handler(v, k):
    print(v, k)


if __name__ == "__main__":
    os_type = OperatingSystemInfo()
    if os_type.is_ubuntu:
        facade_type = UbuntuMouseApiFacadeCore
    elif os_type.is_windows:
        facade_type = WindowsMouseApiFacade
    api_facade = facade_type()
    folder = Path("/tmp")

    clock = Clock()

    try:
        tracker = MouseTrackerCore(
            clock, api_facade, [end_program_readout, pretend_report_event])
        thread_handler = ThreadedTracker(tracker)
        thread_handler.start()
        # Add a way to keep the main thread alive
        while True:
            time.sleep(0.3)
    except KeyboardInterrupt:
        thread_handler.stop()
        # Give the thread time to clean up
        time.sleep(0.3)
