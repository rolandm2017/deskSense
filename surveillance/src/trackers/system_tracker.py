import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
import signal
import sys
import atexit
import threading
import asyncio
from datetime import datetime
from typing import Callable, Awaitable
import concurrent.futures


class SystemPowerTracker:
    def __init__(self, on_shutdown: Callable[[], Awaitable[None]], loop: asyncio.AbstractEventLoop = None):
        self.on_shutdown = on_shutdown
        self.main_loop = None
        self.main_loop_thread = None
        self.asyncio_loop = loop or asyncio.get_event_loop()
        self.log_file = "power_on_off_times.txt"
        self._shutdown_in_progress = False

        # Log startup
        self._log_event("startup")

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._system_shutdown_handler)
        signal.signal(signal.SIGINT, self._system_shutdown_handler)
        signal.signal(signal.SIGHUP, self._system_shutdown_handler)

        # Start sleep detection in a separate thread
        self._setup_sleep_detection()

    def _log_event(self, event_type: str):
        """Log a power-related event to the log file"""
        try:
            with open(self.log_file, "a") as f:
                f.write(
                    f"{event_type} at: {datetime.now().strftime('%m-%d %H:%M:%S')}\n")
        except Exception as e:
            print(f"Failed to log event: {e}")

    def _run_shutdown_in_thread(self):
        """Run shutdown handler in a separate thread"""
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Run the shutdown handler
            loop.run_until_complete(self.on_shutdown())
        except Exception as e:
            print(f"Error in shutdown handler: {e}")
        finally:
            loop.close()

    def _system_shutdown_handler(self, signum, frame):
        """Handler for system shutdown/termination signals"""
        if self._shutdown_in_progress:
            return

        self._shutdown_in_progress = True

        print("###")
        print("### System shutdown detected")
        print("###")
        print(f"Received shutdown signal: {signum}")
        print("Triggering shutdown due to: shutdown")

        try:
            self._log_event("shutdown")
        except Exception as e:
            print(f"Failed to log shutdown: {e}")

        # Run shutdown in a separate thread
        cleanup_thread = threading.Thread(target=self._run_shutdown_in_thread)
        cleanup_thread.start()
        cleanup_thread.join(timeout=2.0)  # Wait up to 2 seconds for cleanup

        if self.main_loop:
            try:
                self.main_loop.quit()
            except:
                pass

        # Now we can exit
        sys.exit(0)

    def _setup_sleep_detection(self):
        """Initialize and start the sleep detection loop in a separate thread"""
        try:
            DBusGMainLoop(set_as_default=True)
            bus = dbus.SystemBus()

            bus.add_signal_receiver(
                self._handle_prepare_for_sleep,
                'PrepareForSleep',
                'org.freedesktop.login1.Manager',
                'org.freedesktop.login1'
            )

            self.main_loop = GLib.MainLoop()
            self.main_loop_thread = threading.Thread(
                target=self.main_loop.run, daemon=True)
            self.main_loop_thread.start()
        except Exception as e:
            print(f"Failed to setup sleep detection: {e}")

    def _handle_prepare_for_sleep(self, sleeping: bool):
        """Handler for sleep/wake signals"""
        if sleeping:
            print(f"System going to sleep at {datetime.now()}")
            self._system_shutdown_handler('sleep', None)
        else:
            print(f"System waking up at {datetime.now()}")
            self._log_event("wake")

    def stop(self):
        """Clean shutdown of the power tracker"""
        if self.main_loop and not self._shutdown_in_progress:
            self.main_loop.quit()
            self.main_loop = None
