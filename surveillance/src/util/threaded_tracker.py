# Old way
import threading
import time


class ThreadedTracker:
    """Wrapper that adds threading behavior"""

    def __init__(self, core_tracker):
        self.core = core_tracker
        self.stop_event = threading.Event()
        self.hook_thread = None
        self.is_running = False

    def start(self):
        """Start the program tracker's threading."""
        self.hook_thread = threading.Thread(target=self._monitor_core)
        self.hook_thread.daemon = True
        self.hook_thread.start()
        self.is_running = True

    def _monitor_core(self):
        while not self.stop_event.is_set():
            self.core.run_tracking_loop()
            time.sleep(0.1)

    def stop(self):
        self.stop_event.set()
        if self.hook_thread is not None and self.hook_thread.is_alive():
            self.hook_thread.join(timeout=1)
        self.is_running = False
