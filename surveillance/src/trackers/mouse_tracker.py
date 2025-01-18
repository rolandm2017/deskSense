# mouse_tracker.py
from enum import Enum, auto
from datetime import datetime

import asyncio

from pathlib import Path
import threading
from threading import Thread
import time


from ..util.detect_os import OperatingSystemInfo
from ..console_logger import ConsoleLogger
from ..facade.mouse_facade import MouseApiFacade, UbuntuMouseApiFacade, WindowsMouseApiFacade

class MouseEvent(str, Enum):
    START = "start"
    STOP = "stop"

class MouseTracker:
    def __init__(self, data_dir, mouse_api_facade, dao, end_program_routine=None):
        """
        Initialize the MouseTracker with Windows event hooks.

        Note that the program starts when the Tracker object is initialized.
        
        Args:
            data_dir (Path): Directory where tracking data will be stored
        """
        self.data_dir = data_dir
        self.mouse_facade: UbuntuMouseApiFacade = mouse_api_facade
        self.mouse_dao = dao
        self.loop = asyncio.get_event_loop()
        # Create a new event loop for this instance
        # self.loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(self.loop)

        self.end_program_func = end_program_routine
        self.environment = OperatingSystemInfo()

        self.movement_start = None
        self.last_position = None
        self.is_moving = False

        self.console_logger = ConsoleLogger()

        self.session_data = []
        self.hook_thread = None  # For thread
        self.mouse_movement_window = "Closed"
        
        self.stop_event = threading.Event()

    def start(self):
        """Start the mouse tracker."""
        self.is_running = True
        # Start the mouse facade's tracking
        self.mouse_facade.start()
        # Start our monitoring thread
        self.hook_thread = threading.Thread(target=self._monitor_mouse)
        self.hook_thread.daemon = True
        self.hook_thread.start()

    def _monitor_mouse(self):
        """Continuously monitor mouse position."""
        while not self.stop_event.is_set():
            current_position = self.mouse_facade.get_position()
            
            is_stopped = not self.is_moving  # avoid reading a negation
            if is_stopped:
                if self.last_position is None or current_position != self.last_position:
                    self.is_moving = True
                    self.movement_start = datetime.now()
                    self.last_position = current_position
            else:
                if current_position == self.last_position:
                    self._handle_mouse_stop(current_position)
                else:
                    self.last_position = current_position
            time.sleep(0.1)  # Polling interval

    def log_movement_to_db(self, start_time, end_time):
        self.loop.create_task(self.mouse_dao.create(start_time, end_time))

    def gather_session(self):
        current = self.session_data
        self.session_data = self.preserve_open_events(current)  # TODO: make currently open mouse movements not be reported, move them to the next interval
        return current
    
    def preserve_open_events(self, current_batch):
        # There can be one or zero open events, not 2.
        to_preserve = []
        if current_batch:
            if current_batch[-1]["event_type"] == MouseEvent.START:
                to_preserve.append(current_batch[-1])
        return to_preserve

    def stop(self):
        """Stop the mouse tracker and clean up."""
        self.stop_event.set()
        self.mouse_facade.stop()  # Stop the facade's tracking
        
        if self.end_program_func:
            self.end_program_func(self.generate_movement_report())
            
        if self.hook_thread is not None and self.hook_thread.is_alive():
            self.hook_thread.join(timeout=1)


def end_program_readout(report):
    # prints the generated report
    ConsoleLogger.log_red(report)


if __name__ == "__main__":
    os_type = OperatingSystemInfo()
    if os_type.is_ubuntu:
        facade_type = UbuntuMouseApiFacade
    elif os_type.is_windows:
        facade_type = WindowsMouseApiFacade
    api_facade = facade_type()
    folder = Path("/tmp")

        
    try:
        instance = MouseTracker(folder, api_facade, end_program_readout)
        # Add a way to keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        instance.stop()
        # Give the thread time to clean up
        time.sleep(0.5)
