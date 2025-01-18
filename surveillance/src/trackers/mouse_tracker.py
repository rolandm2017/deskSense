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
from ..console_logger import ConsoleLogger
from ..facade.mouse_facade import UbuntuMouseApiFacadeCore, WindowsMouseApiFacade

class MouseEvent(str, Enum):
    START = "start"
    STOP = "stop"

class MouseMovementEvent:
    def __init__(self, event_type, position, timestamp):
        self.event_type = event_type
        self.position = position
        self.timestamp = timestamp

class MouseMoveWindow:
    def __init__(self, start_of_window, end_of_window):
        """Where the mouse was is irrelevant. From when to when it was moving is the important part."""
        self.start_time = start_of_window
        self.end_time = end_of_window

    def __str__(self):
        return f"Mouse movement from {self.start_time} to {self.end_time}"

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
        print(coords, '56ru')
        coords.timestamp = self.clock.now()
        return coords  
        
    def position_is_same_as_before(self, new_position):
        return self.last_position.x == new_position.x and self.last_position.y == new_position.y

    def mouse_is_moving(self, coords):
        previous = self.last_position
        is_still_moving = previous.x != coords.x or previous.y != coords.y
        return is_still_moving
    
    def start_tracking_movement(self, latest_result):
        self.console_logger.log_green("[LOG] Start movement window")
        self.is_moving = True
        self.last_position = latest_result
        self.movement_start_time = self.clock.now()
    
    def keep_window_open_and_update(self, latest_reading):
        self.last_position = latest_reading  # I think this is enough

    def close_and_retrieve_window(self, latest_result):
        """Handle the mouse stopping."""
        self.console_logger.log_green("[LOG] End movement window")
        self.is_moving = False
        return MouseMoveWindow(self.movement_start_time, latest_result.timestamp)
    
    def run_tracking_loop(self):
        latest_result = self.get_mouse_position()
        if self.is_moving: 
            has_stopped = self.position_is_same_as_before(latest_result)
            if has_stopped:
                window = self.close_and_retrieve_window(latest_result)
                self.session_data.append(window)
                self.apply_handlers(window)
                self.reset()
            else:
                self.keep_window_open_and_update(latest_result)
        else:
            if self.last_position is None or self.mouse_is_moving(latest_result):
                self.start_tracking_movement(latest_result)

    def reset(self):
        self.movement_start_time = None

    def monitor_mouse(self):
        """The original from before the thread-tracker separation"""
        current_position = self.mouse_facade.get_position_coords()
        # assign time here
        
        if self.is_moving: # avoid reading a negation
            has_stopped = current_position == self.last_position
            if has_stopped:
                self._handle_mouse_stop(current_position)
            else:
                self.last_position = current_position
        else:
            if self.last_position is None or current_position != self.last_position:
                self.is_moving = True
                self.movement_start_time = self.clock.now()
                self.last_position = current_position
    
    def handle_mouse_stop(self, latest_result):
        return self.close_and_retrieve_window(latest_result)  # Alias

    def apply_handlers(self, content):
        if isinstance(self.event_handlers, list):
            for handler in self.event_handlers:
                handler(content)  # emit an event
        else:
            self.event_handlers(content)  # is a single func                

    def gather_session(self):
        current = self.session_data
        return current
        # self.session_data = self.preserve_open_events(current)  # TODO: make currently open mouse movements not be reported, move them to the next interval
        # return current
    
    def preserve_open_events(self, current_batch):
        # FIXME: convert to accept .start_time, .end_time events
        # There can be one or zero open events, not 2.
        to_preserve = []
        if current_batch:
            if current_batch[-1]["event_type"] == MouseEvent.START:
                to_preserve.append(current_batch[-1])
        return to_preserve

    def stop(self):
        if self.end_program_func:
            self.end_program_func(self.generate_movement_report())

    


class ThreadedMouseTracker:
    """Wrapper that adds threading behavior"""
    def __init__(self, core_tracker):
        self.core = core_tracker
        self.stop_event = threading.Event()
        self.hook_thread = None
        self.is_running = False

    def start(self):
        """Start the mouse tracker's threading."""
        self.hook_thread = threading.Thread(target=self._monitor_mouse)
        self.hook_thread.daemon = True
        self.hook_thread.start()
        self.is_running = True
        
    def _monitor_mouse(self):
        while not self.stop_event.is_set():
            self.core.run_tracking_loop()
            # latest_result = self.core.get_mouse_position()
            # if self.core.is_moving: 
            #     has_stopped = self.core.position_is_same_as_before(latest_result)
            #     if has_stopped:
            #         window = self.core.close_and_retrieve_window(latest_result)
            #         self.core.apply_handlers(window)
            #     else:
            #         self.core.keep_window_open_and_update(latest_result)
            # else:
            #     if self.core.last_position is None or self.core.mouse_is_moving(latest_result):
            #         self.core.start_tracking_movement(latest_result)
            
            time.sleep(0.1)

    def stop(self):
        self.stop_event.set()
        if self.hook_thread is not None and self.hook_thread.is_alive():
            self.hook_thread.join(timeout=1)


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
        tracker = MouseTrackerCore(clock, api_facade, [end_program_readout, pretend_report_event])
        thread_handler = ThreadedMouseTracker(tracker)
        thread_handler.start()
        # Add a way to keep the main thread alive
        while True:
            time.sleep(0.3)
    except KeyboardInterrupt:
        thread_handler.stop()
        # Give the thread time to clean up
        time.sleep(0.3)
