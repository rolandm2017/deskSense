import signal

from win32gui import PumpMessages
from win32con import WM_POWERBROADCAST, PBT_APMSUSPEND, PBT_APMRESUMESUSPEND
from win32gui import CreateWindow, WNDCLASS, RegisterClass, DefWindowProc
from win32api import PostQuitMessage

from ctypes import windll, WINFUNCTYPE, POINTER, wintypes

import sys
import ctypes
import logging
import asyncio
from datetime import datetime

from typing import Callable, Awaitable, Optional

import time


from ..db.models import SystemStatus

from ..object.enums import SystemStatusType


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Windows API setup
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def on_exit(signum, frame):
    logging.info("Process exiting...")
    sys.exit(0)

class WindowsSystemPowerTracker:
    def __init__(self, 
                 on_shutdown: Callable[[], Awaitable[None]],
                 system_status_dao,
                 check_session_integrity,
                 loop: Optional[asyncio.AbstractEventLoop] = None,
                 log_file: Optional[str] = None):
        """Tries to do the same thing as Ubuntu's power tracker, but on Windows"""
        self.on_shutdown = on_shutdown
        self.system_status_dao = system_status_dao
        self.check_session_integrity = check_session_integrity

        self.asyncio_loop = loop or asyncio.get_event_loop()

        # State tracking
        self._shutdown_in_progress = False

        self._register_event_hooks()
        # self._log_startup_status()
        # self._check_session_integrity()

        self._setup_signal_handlers()
        self._setup_sleep_detection()

        right_now = datetime.now()

        self.asyncio_loop.create_task(self._log_startup_status(right_now))
        self.asyncio_loop.create_task(self._check_session_integrity(right_now))

        signal.signal(signal.SIGINT, self._handle_exit)
        signal.signal(signal.SIGTERM, self._handle_exit)

    def _register_event_hooks(self):
        self._power_notify_handle = ctypes.windll.user32.RegisterPowerSettingNotification(
            ctypes.windll.kernel32.GetConsoleWindow(),
            ctypes.byref(wintypes.GUID('{5D3E9A59-E9D5-4B00-A6BD-FF34FF516548}')),
            0
        )

    def _handle_shutdown_signal(self, signum, frame):
        """Handle shutdown signals (SIGTERM, SIGINT, SIGHUP)"""
        # Prevent multiple shutdown attempts
        if self._shutdown_in_progress:
            return
        self._shutdown_in_progress = True

    def _setup_signal_handlers(self):
        """Sets up signal handlers to gracefully handle termination signals (CTRL+C, termination events, etc.)."""
        signal.signal(signal.SIGINT, self._handle_exit)  # Handles CTRL+C
        signal.signal(signal.SIGTERM, self._handle_exit) # Handles termination requests
        windll.kernel32.SetConsoleCtrlHandler(
            WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD)(self._handle_console_signal), True
        )

    def _setup_sleep_detection(self):
        """
        Sets up a hidden window to listen for Windows power events (sleep/wake notifications).
        """
      
        
        def wnd_proc(hwnd, msg, wparam, lparam):
            """
            Window procedure to handle power-related messages.
            
            Args:
                hwnd: Window handle.
                msg: Message identifier.
                wparam: First message parameter.
                lparam: Second message parameter.
            
            Returns:
                Default window procedure response.
            """
            if msg == WM_POWERBROADCAST:
                if wparam == PBT_APMSUSPEND:
                    self.system_status_dao.create_status(SystemStatusType.SLEEP)
                elif wparam == PBT_APMRESUMESUSPEND:
                    self.system_status_dao.create_status(SystemStatusType.WAKE)
            return DefWindowProc(hwnd, msg, wparam, lparam)
        
        class_name = "PowerNotifyWindow"
        wnd_class = WNDCLASS()
        wnd_class.lpfnWndProc = wnd_proc
        wnd_class.lpszClassName = class_name
        RegisterClass(wnd_class)
        hwnd = CreateWindow(class_name, "PowerNotify", 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        def listen_for_events():
            """
            Starts an event listener loop to process system power events.
            """
            try:
                PumpMessages()
            except KeyboardInterrupt:
                PostQuitMessage(0)
        
        import threading
        threading.Thread(target=listen_for_events, daemon=True).start()


    def _setup_sleep_detection(self):
        """Detect when Windows is going to sleep"""
        pass

    def _handle_exit(self, signum, frame):
        self._run_shutdown_tasks()
        sys.exit(0)

    def _run_shutdown_tasks(self):
        self.system_status_dao.create_status(SystemStatusType.SHUTDOWN)
        self.on_shutdown()

    async def _log_startup_status(self):
        await self.system_status_dao.create_status(SystemStatusType.STARTUP)

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

    def on_shutdown(self):
        print("System is shutting down...")

    def listen(self):
        print("Listening for system power events...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self._handle_exit(signal.SIGINT, None)