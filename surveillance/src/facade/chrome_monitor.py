
import psutil
from typing import Dict, Optional
from datetime import datetime


from .program_facade import ProgramApiFacadeCore


class ChromeMonitor:
    def __init__(self, program_api_facade: ProgramApiFacadeCore):
        self.facade = program_api_facade
        self.chrome_processes = set()
        self._update_chrome_processes()

    def _update_chrome_processes(self):
        """Update the set of currently running Chrome processes."""
        self.chrome_processes.clear()
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                # Chrome process names vary by OS
                if proc.name().lower() in ['chrome.exe', 'google-chrome', 'google-chrome-stable']:
                    self.chrome_processes.add(proc.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    def register_chrome_close_callback(self, callback):
        """Register a callback to be called when Chrome closes.

        Args:
            callback: Function to be called with chrome_info dict when Chrome closes.
                     chrome_info contains 'time', 'pid', and 'exit_code' if available.
        """
        import threading
        self.callback = callback
        self.monitor_thread = threading.Thread(
            target=self._monitor_chrome, daemon=True)
        self.monitor_thread.start()

    def _monitor_chrome(self):
        """Monitor Chrome processes and detect when they close."""
        while True:
            previous_processes = self.chrome_processes.copy()
            self._update_chrome_processes()

            # Check for closed processes
            closed_processes = previous_processes - self.chrome_processes
            if closed_processes:
                for pid in closed_processes:
                    chrome_info = {
                        'time': datetime.now(),
                        'pid': pid,
                        'exit_code': None  # Could potentially get this from process object if needed
                    }
                    try:
                        self.callback(chrome_info)
                    except Exception as e:
                        self.facade.console_logger.log(
                            f"Error in chrome close callback: {str(e)}")

            # Sleep to prevent high CPU usage
            import time
            time.sleep(1)


# Example usage:
"""
def on_chrome_close(chrome_info):
    print(f"Chrome closed at {chrome_info['time']} (PID: {chrome_info['pid']})")

# Initialize the monitor
os_info = YourOSInfoClass()  # You'll need to provide this
program_facade = ProgramApiFacadeCore(os_info)
chrome_monitor = ChromeMonitor(program_facade)

# Register the callback
chrome_monitor.register_chrome_close_callback(on_chrome_close)

# Keep the main thread running
while True:
    time.sleep(1)
"""
