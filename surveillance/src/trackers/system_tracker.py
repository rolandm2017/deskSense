import asyncio
import signal
import threading
import os
import psutil
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib  # type: ignore
from datetime import datetime
from typing import Callable, Awaitable, Optional

from ..db.models import SystemStatus

from ..object.enums import SystemStatusType


class SystemPowerTracker:
    def __init__(self,
                 on_shutdown: Callable[[], Awaitable[None]],
                 system_status_dao,
                 check_session_integrity,
                 loop: Optional[asyncio.AbstractEventLoop] = None,
                 log_file: Optional[str] = None):
        """
        Initialize the system power tracker.

        Args:
            system_status_dao: DAO for recording system status events
            on_shutdown: Callback to run when shutting down
            loop: Asyncio event loop (or default if None)
            log_file: Optional file path for debug logging
        """
        print("[info] Claude's power tracker!")

        # Core properties
        self.on_shutdown = on_shutdown
        self.asyncio_loop = loop or asyncio.get_event_loop()
        self.log_file = log_file

        system_status_dao.accept_power_tracker_loop(self.asyncio_loop)

        self.system_status_dao = system_status_dao
        self.signal_check_session_integrity = check_session_integrity
        # State tracking
        self._shutdown_in_progress = False
        self._shutdown_complete = threading.Event()

        # Setup signals and sleep detection
        self._setup_signal_handlers()
        self._setup_sleep_detection()

        # Log startup immediately
        self._log_event("startup")
        right_now = datetime.now()
        self.asyncio_loop.create_task(self._log_startup_status(right_now))
        self.asyncio_loop.create_task(self._check_session_integrity(right_now))

    async def _log_startup_status(self, latest_startup_time):
        """Record startup in the database"""
        await self.system_status_dao.create_status(SystemStatusType.STARTUP, latest_startup_time)

    async def _check_session_integrity(self, latest_startup_time):
        """
        Signal system ready for integrity check.

        Code ultimately sends a response to ... "audit_sessions" in SessionIntegrityDAO.
        """
        latest_shutdown_log: SystemStatus | None = await self.system_status_dao.read_latest_shutdown()
        if latest_shutdown_log:
            self.signal_check_session_integrity(
                latest_shutdown_log.created_at, latest_startup_time)
        else:
            no_shutdown_found: None = latest_shutdown_log
            self.signal_check_session_integrity(
                no_shutdown_found, latest_startup_time)

    def _log_event(self, event_type: str):
        """Log event to debug file if configured"""
        if not self.log_file:
            return

        try:
            with open(self.log_file, "a") as f:
                f.write(
                    f"{event_type} at: {datetime.now().strftime('%m-%d %H:%M:%S')}\n")
        except Exception as e:
            print(f"Failed to log event: {e}")

    def _setup_signal_handlers(self):
        """Set up OS signal handlers"""
        signal.signal(signal.SIGTERM, self._handle_shutdown_signal)
        signal.signal(signal.SIGINT, self._handle_shutdown_signal)
        signal.signal(signal.SIGHUP, self._handle_shutdown_signal)

    def _setup_sleep_detection(self):
        """Initialize sleep detection using dbus"""
        try:
            DBusGMainLoop(set_as_default=True)
            bus = dbus.SystemBus()
            bus.add_signal_receiver(
                self._handle_sleep_signal,
                'PrepareForSleep',
                'org.freedesktop.login1.Manager',
                'org.freedesktop.login1'
            )

            # Run GLib main loop in a daemon thread
            self.main_loop = GLib.MainLoop()
            self.main_loop_thread = threading.Thread(
                target=self.main_loop.run, daemon=True)
            self.main_loop_thread.start()
        except Exception as e:
            print(f"Failed to setup sleep detection: {e}")
            self.main_loop = None
            self.main_loop_thread = None

    def _handle_shutdown_signal(self, signum, frame):
        """Handle shutdown signals (SIGTERM, SIGINT, SIGHUP)"""
        # Prevent multiple shutdown attempts
        if self._shutdown_in_progress:
            return
        self._shutdown_in_progress = True

        print(signum, "HERE 113ru")

        # Determine reason and status type based on signal
        if signum == 15:  # SIGTERM
            reason = "restart program"
            status_type = SystemStatusType.HOT_RELOAD_STARTED
        elif signum == 2:  # SIGINT
            reason = "Ctrl+C or Interrupt"
            status_type = SystemStatusType.CTRL_C_SIGNAL
        elif signum == 1:  # SIGHUP
            reason = "Terminal closed"
            status_type = SystemStatusType.SHUTDOWN
        else:
            reason = f"Unknown signal: {signum}"
            with open("unkown_signal_logs.txt", "a") as f:
                f.write("\n" + str(signum) + "\n")
            status_type = SystemStatusType.SHUTDOWN

        print(f"\n### System shutdown detected (signal {signum})")
        print(f"Triggering shutdown due to: {reason}")

        # Run shutdown tasks
        print(self._initiate_shutdown, '135ru')
        self._initiate_shutdown(status_type, reason)

    def _handle_sleep_signal(self, sleeping: bool):
        """Handle sleep/wake signals from dbus"""
        if sleeping:
            print(f"System going to sleep at {datetime.now()}")
            self._initiate_shutdown(SystemStatusType.SLEEP, "System sleep")
        else:
            print(f"System waking up at {datetime.now()}")
            # Note: This runs on wake and doesn't need to block
            asyncio.run_coroutine_threadsafe(
                self.system_status_dao.create_status(
                    SystemStatusType.WAKE, datetime.now()),
                self.asyncio_loop
            )
            self._log_event("wake")

    def _initiate_shutdown(self, status_type: SystemStatusType, reason: str):
        """Common code path for all shutdown scenarios"""
        # Log the event
        self._log_event(reason)

        print(f"Initiating shutdown with status: {status_type}")

        # Create a new thread to handle the shutdown process
        # This ensures the main thread can respond to signals and doesn't get blocked
        shutdown_thread = threading.Thread(
            target=self._run_shutdown_in_thread,
            args=(status_type, reason)
        )
        shutdown_thread.start()

        # Wait for the shutdown thread to complete
        # Use a shorter timeout for sleep events
        timeout = 5.0 if status_type != SystemStatusType.SLEEP else 1.0
        print(f"Waiting up to {timeout}s for shutdown tasks to complete...")
        shutdown_thread.join(timeout=timeout)

        if shutdown_thread.is_alive():
            print("Warning: Shutdown tasks did not complete in time")
        else:
            print("Shutdown tasks completed successfully")

        # Perform final cleanup
        print("Running final cleanup")
        self._perform_final_cleanup(status_type)

    def _run_shutdown_in_thread(self, status_type: SystemStatusType, reason: str):
        """Run shutdown tasks in a dedicated thread"""
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        print(
            f"Current loop in shutdown thread: {id(asyncio.get_event_loop())}")

        print(f"Thread ID for shutdown: {threading.get_ident()}")

        try:
            # Tell the DAO about our loop
            self.system_status_dao.accept_power_tracker_loop(loop)

            # Run our async tasks in the new loop
            print(f"Thread started for shutdown tasks: {status_type}")
            loop.run_until_complete(
                self._run_shutdown_tasks(status_type, reason))
            print("Thread completed all shutdown tasks")
        except Exception as e:
            print(f"Error in shutdown thread: {e}")
        finally:
            loop.close()

    async def _run_shutdown_tasks(self, status_type: SystemStatusType, reason: str):
        """Run all shutdown-related async tasks"""
        print(f"Starting shutdown tasks, status: {status_type}")
        success = await self.system_status_dao.create_status(status_type, datetime.now())

        if success:
            print("Database write completed successfully")
        else:
            print("Database write failed")

        try:
            print("Running on_shutdown callback...")
            await self.on_shutdown()
            print("on_shutdown callback completed!")
        except Exception as callback_error:
            print(f"on_shutdown callback failed: {callback_error}")

        print("All shutdown tasks completed")

    def _perform_final_cleanup(self, status_type):
        """Final cleanup operations before exiting"""
        print(f"Final cleanup for status: {status_type}")

        # Stop the main loop if it's running
        if hasattr(self, 'main_loop') and self.main_loop:
            self.main_loop.quit()

        # Clean up child processes
        try:
            current_pid = os.getpid()
            for child in psutil.Process(current_pid).children(recursive=True):
                child.terminate()
                try:
                    child.wait(timeout=0.2)  # Short timeout
                except psutil.TimeoutExpired:
                    child.kill()
        except Exception as e:
            print(f"Error cleaning up processes: {e}")

        # Only exit on actual shutdown (not sleep)
        # This was comparing to a string when it should be comparing to enum value
        if status_type != SystemStatusType.SLEEP:
            print("Shutdown complete.")
            os._exit(0)

    async def stop(self):
        """Gracefully stop the tracker (for manual shutdown)"""
        if not self._shutdown_in_progress:
            self._shutdown_in_progress = True
            await self._run_shutdown_tasks(SystemStatusType.SHUTDOWN, "Manual stop")
            if self.main_loop:
                self.main_loop.quit()
