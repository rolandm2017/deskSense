# mouse_tracker.py
from enum import Enum, auto
from datetime import datetime
import csv
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
    MOVE = "move"

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

    def _log_movement_to_csv(self, event_type, position):
        """
        Log mouse movement events to CSV.
        
        Args:
            event_type (str): Either 'start' or 'stop'
            position (tuple): (x, y) coordinates of mouse position
        """
        # print("Not intended for use")
        date_str = datetime.now().strftime('%Y-%m-%d')
        file_path = self.data_dir / f'mouse_tracking_{date_str}.csv'
        
        # Create file with headers if it doesn't exist
        if not file_path.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)  # Create directories if needed
            with open(file_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['timestamp', 'event_type', 'x_position', 'y_position'])
                writer.writeheader()
        
        # Log the event
        event = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'x_position': position[0],
                'y_position': position[1]
            }
        with open(file_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'event_type', 'x_position', 'y_position'])
            writer.writerow(event)

        self.session_data.append(event)

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

    def generate_movement_report(self, date_str=None):
        """
        Generate a report of mouse movement patterns for a specific date.
        
        Args:
            date_str (str): Date in format 'YYYY-MM-DD'. If None, uses current date.
        
        Returns:
            dict: Report containing movement statistics
        """
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
            
        file_path = self.data_dir / f'mouse_tracking_{date_str}.csv'
        if not file_path.exists():
            return "No mouse tracking data available for this date."
            
        movement_sessions = []
        start_time = None
        
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['event_type'] == 'start':
                    start_time = datetime.fromisoformat(row['timestamp'])
                elif row['event_type'] == 'stop' and start_time:
                    end_time = datetime.fromisoformat(row['timestamp'])
                    duration = (end_time - start_time).total_seconds()
                    movement_sessions.append(duration)
                    start_time = None
        
        if not movement_sessions:
            return {
                'date': date_str,
                'total_movements': 0,
                'avg_movement_duration': 0,
                'total_movement_time': 0
            }
            
        return {
            'date': date_str,
            'total_movements': len(movement_sessions),
            'avg_movement_duration': round(sum(movement_sessions) / len(movement_sessions), 2),
            'total_movement_time': round(sum(movement_sessions), 2)
        }
    


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
