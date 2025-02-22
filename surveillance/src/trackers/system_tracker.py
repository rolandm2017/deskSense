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


class SystemPowerTracker:
    def __init__(self, on_shutdown: Callable[[], Awaitable[None]], loop: asyncio.AbstractEventLoop = None):
        self.on_shutdown = on_shutdown
        self.main_loop = None
        self.main_loop_thread = None
        self.asyncio_loop = loop or asyncio.get_event_loop()
        self.log_file = "power_on_off_times.txt"
        self._shutdown_in_progress = False
        self._shutdown_event = threading.Event()

        # Log startup
        self._log_event("startup")

        # Register signal handlers
        signal.signal(signal.SIGTERM, self._system_shutdown_handler)
        signal.signal(signal.SIGINT, self._system_shutdown_handler)
        signal.signal(signal.SIGHUP, self._system_shutdown_handler)

        # Register exit handler
        atexit.register(self._exit_handler)

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

    async def _run_shutdown_handler(self):
        """Run the shutdown handler and wait for it to complete"""
        if not hasattr(self.on_shutdown, '__call__'):
            print("Warning: shutdown handler is not callable")
            return

        try:
            await self.on_shutdown()
        except Exception as e:
            print(f"Error in shutdown handler: {e}")

    def _trigger_shutdown(self, reason: str):
        """Helper to trigger shutdown from any context"""
        if self._shutdown_in_progress:
            return

        self._shutdown_in_progress = True
        print(f"Triggering shutdown due to: {reason}")

        try:
            self._log_event(reason)
        except Exception as e:
            print(f"Failed to log shutdown: {e}")

        try:
            if not self.asyncio_loop.is_closed():
                future = asyncio.run_coroutine_threadsafe(
                    self._run_shutdown_handler(),
                    self.asyncio_loop
                )

                try:
                    future.result(timeout=5.0)  # 5 second timeout
                except asyncio.TimeoutError:
                    print("Warning: Shutdown handler timed out")
                except Exception as e:
                    print(f"Error during shutdown: {e}")
        except Exception as e:
            print(f"Failed to run shutdown handler: {e}")

        self._shutdown_event.set()

    def _setup_sleep_detection(self):
        """Initialize and start the sleep detection loop in a separate thread"""
        try:
            DBusGMainLoop(set_as_default=True)
            bus = dbus.SystemBus()

            # Connect to logind
            bus.add_signal_receiver(
                self._handle_prepare_for_sleep,  # callback
                'PrepareForSleep',               # signal name
                'org.freedesktop.login1.Manager',  # interface
                'org.freedesktop.login1'         # path
            )

            # Start GLib main loop in a separate thread
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
            self._trigger_shutdown("sleep")
        else:
            print(f"System waking up at {datetime.now()}")
            self._log_event("wake")

    def _system_shutdown_handler(self, signum, frame):
        """Handler for system shutdown/termination signals"""
        if self._shutdown_in_progress:
            return

        print("###")
        print("### System shutdown detected")
        print("###")
        print(f"Received shutdown signal: {signum}")

        self._trigger_shutdown("shutdown")

        # Wait for shutdown to complete or timeout
        self._shutdown_event.wait(timeout=5.0)

        if self.main_loop:
            try:
                self.main_loop.quit()
            except:
                pass

        sys.exit(0)

    def _exit_handler(self):
        """Handler for normal program termination"""
        if not self._shutdown_in_progress:
            print("Program is exiting!")
            self._trigger_shutdown("exit")
            if self.main_loop:
                try:
                    self.main_loop.quit()
                except:
                    pass

    def stop(self):
        """Clean shutdown of the power tracker"""
        if self.main_loop and not self._shutdown_in_progress:
            self.main_loop.quit()
            self.main_loop = None
