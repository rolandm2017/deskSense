import ctypes
from ctypes import wintypes

import psutil  # type: ignore -> can't import on ubuntu
import win32api  # type: ignore -> can't import on ubuntu
import win32con  # type: ignore -> can't import on ubuntu
import win32gui  # type: ignore -> can't import on ubuntu
import win32process  # type: ignore -> can't import on ubuntu

import time

from typing import Dict, Generator, List, TypedDict

from activitytracker.object.classes import ProgramSessionDict
from activitytracker.util.console_logger import ConsoleLogger

from .program_facade_base import ProgramFacadeInterface


class WindowsProgramFacadeCore(ProgramFacadeInterface):
    def __init__(self):
        self.console_logger = ConsoleLogger()
        self.win32gui = win32gui
        self.win32process = win32process
        self.previous_window = None

    def listen_for_window_changes(self) -> Generator[ProgramSessionDict, None, None]:
        """
        Listens for window focus changes and yields window information when changes occur.
        """
        # We'll use polling to detect window changes since it's simpler than
        # setting up a Windows event hook
        self.previous_window = self.win32gui.GetForegroundWindow()

        # TODO: Change to a hook
        while True:
            time.sleep(0.5)  # Check every half second

            current_window = self.win32gui.GetForegroundWindow()

            # If the window has changed
            if current_window != self.previous_window:
                self.previous_window = current_window
                # It does call getForegroundWindow a second time. that's OK
                window_info = self._read_windows()
                self.console_logger.debug(
                    f"Window changed: {window_info['window_title']} ({window_info['process_name']})"
                )
                yield window_info

    def _read_windows(self) -> ProgramSessionDict:
        """
        Reads information about the currently active window on Windows.
        """
        window = self.win32gui.GetForegroundWindow()

        # Check if the window handle is valid
        invalid_window = window == 0
        if invalid_window:
            return {
                "os": "Windows",
                "pid": None,
                "process_name": "No foreground window",
                "exe_path": "No foreground window",
                "window_title": "",
            }
        # pid = self.win32process.GetWindowThreadProcessId(window)[1]

        try:
            _, pid = self.win32process.GetWindowThreadProcessId(window)

            # Sanity check on the PID
            if pid <= 0:
                self.console_logger.debug("Invalid window:")
                self.console_logger.debug("Sub zero PID")
                self.console_logger.debug(window)
                return {
                    "os": "Windows",
                    "pid": None,
                    "process_name": "Invalid process",
                    "exe_path": "Invalid",
                    "window_title": self.win32gui.GetWindowText(window),
                }
            # FIXME: ValueError: pid must be a positive integer (got -516382288)
            # FIXME: ValueError: pid must be a positive integer (got -1313135248)
            # FIXME: ValueError: pid must be a positive integer (got -792075456
            # FIXME: Think the above errors happeneed while starting up pc
            process = psutil.Process(pid)
            exe_path = process.exe()  # This gets the full path to the executable
            process_name = process.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            process_name = "Unknown"

        return {
            "os": "Windows",
            "pid": pid,
            "process_name": process_name,
            "exe_path": exe_path,
            "window_title": self.win32gui.GetWindowText(window),
        }

    def setup_window_hook(self):
        """
        Alternative implementation using Windows hooks for more efficient window change detection.
        This method sets up a Windows hook that triggers on window focus changes.

        The hook will run only when my operating system tells my program that the window changed focus.

        """
        pass  # Note that the implementation exists in git
