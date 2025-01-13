from datetime import datetime, timedelta
import csv
from threading import Thread
import time

from .console_logger import ConsoleLogger
from facade.keyboard_facade import KeyboardApiFacade
from .util import InterruptHandler

DELAY_TO_AVOID_CPU_HOGGING = 0.01

class KeyboardTracker:
    def __init__(self, data_dir, keyboard_api_facade, interrupt_handler):
        self.events = []
        self.data_dir = data_dir
        
        # so surveillanceManager can grab the interval data
        self.session_data = []
        self.console_logger = ConsoleLogger()
        self.recent_count = 0
        self.time_of_last_terminal_out = datetime.now()

        self.keyboard_facade: KeyboardApiFacade = keyboard_api_facade

        # Initialize interrupt handler with cleanup callback
        self.interrupt_handler = interrupt_handler(cleanup_callback=self.stop)

        self.is_running = False
        self.monitor_thread = None
        self.start()

    def start(self):
        self.is_running = True
        self.monitor_thread = Thread(target=self._monitor_keyboard)
        self.monitor_thread.daemon = True  # Thread will exit when main program exits
        self.monitor_thread.start()

    def _monitor_keyboard(self):
        while self.is_running:
            event = self.keyboard_facade.read_event()
            if self.keyboard_facade.event_type_is_key_down(event.event_type):
                current_time = datetime.now()
                self._log_event_to_csv(current_time)
                self.recent_count += 1  # per keystroke
                if self._is_ready_to_log_to_console(current_time): 
                    # @@@@
                    # Please never log the actual key pressed
                    # @@@@
                    self.console_logger.log_key_presses(self.recent_count)
                    self.recent_count = 0
                    self.time_of_last_terminal_out = current_time

            time.sleep(DELAY_TO_AVOID_CPU_HOGGING)  # Small sleep to prevent CPU hogging

    def _log_event_to_csv(self, current_time):
        self.events.append(current_time)

        date_str = current_time.strftime('%Y-%m-%d')
        file_path = self.data_dir / f'key_logging_{date_str}.csv'

        # Create file with headers if it doesn't exist
        if not file_path.exists():
            with open(file_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['date', 'timestamp'])
                writer.writeheader()
        
        # Log the event
        with open(file_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['date', 'timestamp'])
            writer.writerow({
                'date': date_str,
                'timestamp': current_time
            })

    def _is_ready_to_log_to_console(self, current_time):
        # log key presses every 3 sec
        return (current_time - self.time_of_last_terminal_out) >= timedelta(seconds=3)
        
    def gather_session(self):
        current = self.session_data
        self.session_data = []
        return current

    def stop(self):
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join()

    def generate_keyboard_report(self):
        return {"total_inputs": len(self.events)}