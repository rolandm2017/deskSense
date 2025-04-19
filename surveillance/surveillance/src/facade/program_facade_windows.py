import psutil
import win32api
import win32con
import win32gui
import win32process

import ctypes
from ctypes import wintypes
import time

from typing import Dict, Generator

from .program_facade_base import ProgramFacadeInterface

from surveillance.src.util.console_logger import ConsoleLogger


class WindowsProgramFacadeCore(ProgramFacadeInterface):
    def __init__(self):
        self.console_logger = ConsoleLogger()
        self.win32gui = win32gui
        self.win32process = win32process
        self.previous_window = None

    def read_current_program_info(self) -> Dict:
        """
        Gets information about the currently active window.

        Returns:
            Dict: Information about the active window including OS, PID, process name, and window title.
        """
        return self._read_windows()

    def _read_windows(self) -> Dict:
        """
        Reads information about the currently active window on Windows.

        Returns:
            Dict: Window information including OS, PID, process name, and window title.
        """
        window = self.win32gui.GetForegroundWindow()

        # Check if the window handle is valid
        invalid_window = window == 0
        if invalid_window:
            return {
                "os": "Windows",
                "pid": None,
                "process_name": "No foreground window",
                "window_title": ""
            }
        # pid = self.win32process.GetWindowThreadProcessId(window)[1]

        try:
            thread_id, pid = self.win32process.GetWindowThreadProcessId(window)

            # Sanity check on the PID
            if pid <= 0:
                self.console_logger.debug("Invalid window:")
                self.console_logger.debug(window, "Sub zero PID")
                return {
                    "os": "Windows",
                    "pid": None,
                    "process_name": "Invalid process",
                    "window_title": self.win32gui.GetWindowText(window)
                }
            # FIXME: ValueError: pid must be a positive integer (got -516382288)
            # FIXME: ValueError: pid must be a positive integer (got -1313135248)
            # FIXME: ValueError: pid must be a positive integer (got -792075456
            # FIXME: Think the above errors happeneed while starting up pc
            process = psutil.Process(pid)
            process_name = process.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            process_name = "Unknown"

        return {
            "os": "Windows",
            "pid": pid,
            "process_name": process_name,
            "window_title": self.win32gui.GetWindowText(window)
        }

    def listen_for_window_changes(self) -> Generator[Dict, None, None]:
        """
        Listens for window focus changes and yields window information when changes occur.

        Yields:
            Dict: Information about the new active window after each focus change.
        """
        # We'll use polling to detect window changes since it's simpler than
        # setting up a Windows event hook
        self.previous_window = self.win32gui.GetForegroundWindow()

        while True:
            time.sleep(0.5)  # Check every half second

            current_window = self.win32gui.GetForegroundWindow()

            # If the window has changed
            if current_window != self.previous_window:
                self.previous_window = current_window
                window_info = self._read_windows()
                self.console_logger.debug(
                    f"Window changed: {window_info['window_title']} ({window_info['process_name']})")
                yield window_info

    def setup_window_hook(self) -> Generator[Dict, None, None]:
        """
        Alternative implementation using Windows hooks for more efficient window change detection.
        This method sets up a Windows hook that triggers on window focus changes.

        The hook will run only when my operating system tells my program that the window changed focus.

        Yields:
            Dict: Information about the new active window after each focus change.


        """
        # Define callback function for window events
        def win_event_callback(hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
            if event == win32con.EVENT_SYSTEM_FOREGROUND:
                window_info = self._read_windows()
                self.console_logger.debug(
                    f"Window changed: {window_info['window_title']} ({window_info['process_name']})")
                # Since we can't yield from a callback, we'll need to store this information
                # and have the main loop check for it
                self.latest_window_info = window_info

        # Convert Python callback to C-compatible callback
        WinEventProc = ctypes.WINFUNCTYPE(
            None,
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.HWND,
            wintypes.LONG,
            wintypes.LONG,
            wintypes.DWORD,
            wintypes.DWORD
        )
        callback = WinEventProc(win_event_callback)

        # Set up the event hook
        hook = win32api.SetWinEventHook(
            win32con.EVENT_SYSTEM_FOREGROUND,
            win32con.EVENT_SYSTEM_FOREGROUND,
            0,
            callback,
            0,
            0,
            win32con.WINEVENT_OUTOFCONTEXT
        )

        self.latest_window_info = None

        try:
            # Message pump to keep the hook active
            msg = ctypes.wintypes.MSG()
            while True:
                if self.latest_window_info:
                    window_info = self.latest_window_info
                    self.latest_window_info = None
                    yield window_info

                # Process Windows messages to keep the hook active
                if ctypes.windll.user32.PeekMessageW(ctypes.byref(msg), 0, 0, 0, 1):
                    ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                    ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
                else:
                    time.sleep(0.1)  # Sleep to avoid high CPU usage
        finally:
            # Clean up the hook when done
            win32api.UnhookWinEvent(hook)
