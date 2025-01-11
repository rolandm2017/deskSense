from datetime import datetime
import keyboard
import csv
from threading import Thread
import time
import signal

DELAY_TO_AVOID_CPU_HOGGING = 0.01

class KeyboardTracker:
    def __init__(self, data_dir):
        self.events = []
        self.data_dir = data_dir

        # so surveillanceManager can grab the interval data
        self.session_data = []

        signal.signal(signal.SIGINT, self._handle_interrupt)  # avoid capturing interrupt

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
            event = keyboard.read_event()
            if event.event_type == keyboard.KEY_DOWN:
                self._log_event()
            time.sleep(DELAY_TO_AVOID_CPU_HOGGING)  # Small sleep to prevent CPU hogging

    def _log_event(self):
        current_time = datetime.now()
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

    def gather_session(self):
        current = self.session_data
        self.session_data = []
        return current
    
    def _handle_interrupt(self, signum, frame):
        print("\nReceived interrupt signal. Cleaning up...")
        self.stop()
        # Re-raise the signal after cleanup
        signal.default_int_handler(signum, frame)

    def stop(self):
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join()

    def generate_keyboard_report(self):
        return {"total_inputs": len(self.events)}