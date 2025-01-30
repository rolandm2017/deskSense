import signal
import sys
import atexit
from typing import Callable


class SystemPowerTracker:
    def __init__(self, on_shutdown: Callable[[], None]):
        self.on_shutdown = on_shutdown

        # Register signal handlers
        signal.signal(signal.SIGTERM, self._system_shutdown_handler)
        signal.signal(signal.SIGINT, self._system_shutdown_handler)
        signal.signal(signal.SIGHUP, self._system_shutdown_handler)

        # Register exit handler
        atexit.register(self._exit_handler)

    def _system_shutdown_handler(self, signum, frame):
        """Handler for system shutdown/termination signals"""
        print("System shutdown detected!")
        # Add your cleanup code here
        print(f"Received shutdown signal: {signum}")
        self.on_shutdown()
        # e.g., save productivity data, close files, etc.
        sys.exit(0)

    def _exit_handler(self):
        """Handler for normal program termination"""
        print("Program is exiting!")
        # Add cleanup code here too
