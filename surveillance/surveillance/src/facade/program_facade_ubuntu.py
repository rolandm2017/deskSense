import psutil
from Xlib import display, X
import subprocess
from typing import Dict, Optional, Generator, cast

from .program_facade_base import ProgramFacadeInterface

from surveillance.src.util.console_logger import ConsoleLogger
from surveillance.src.object.classes import ProgramSessionDict


class UbuntuProgramFacadeCore(ProgramFacadeInterface):
    def __init__(self):
        self.console_logger = ConsoleLogger()
        self.display = display
        self.X = X

    def read_current_program_info(self) -> ProgramSessionDict:
        return self._read_focused_program()

    def listen_for_window_changes(self) -> Generator[ProgramSessionDict, None, None]:
        """
        Listens for window focus changes and yields window information when changes occur.

        Yields:
            Dict: Information about the new active window after each focus change.
        """
        d = self.display.Display()
        root = d.screen().root

        # Listen for focus change events
        root.change_attributes(
            event_mask=self.X.FocusChangeMask | self.X.PropertyChangeMask)

        while True:
            event = d.next_event()
            if event.type == self.X.PropertyNotify:
                if event.atom == d.intern_atom('_NET_ACTIVE_WINDOW'):
                    # Window focus changed - get new window info
                    window_info = self._read_focused_program()
                    self.console_logger.debug(
                        f"Window changed: {window_info['window_title']} ({window_info['process_name']})")
                    yield window_info

    def _read_focused_program(self) -> ProgramSessionDict:
        """
        Reads information about the currently active window on Ubuntu.

        Returns:
            Dict: Window information including OS, PID, process name, executable path, and window title.
        """
        try:
            # Get active window info
            window_info = self._get_active_window_info()

            if window_info is None:
                return {
                    "os": "Ubuntu",
                    "pid": None,
                    "process_name": "Unknown",
                    "exe_path": "Unknown",
                    "window_title": "No active window"
                }

            pid = window_info["pid"]
            process_name = window_info["name"]
            window_title = window_info["title"]

            # Get executable path
            exe_path = "Unknown"
            if pid is not None:
                try:
                    exe_path = self.read_exe_path_for_pid(pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    self.console_logger.debug(
                        f"Could not access process with PID {pid}")

            return {
                "os": "Ubuntu",
                "pid": pid,
                "process_name": process_name,
                "exe_path": exe_path,
                "window_title": window_title
            }

        except Exception as e:
            self.console_logger.debug(f"Error in _read_ubuntu: {str(e)}")
            return {
                "os": "Ubuntu",
                "pid": None,
                "process_name": "Error",
                "exe_path": "Error",
                "window_title": f"Error: {str(e)}"
            }

    def _get_active_window_info(self) -> Optional[Dict]:
        """
        Gets detailed information about the active window including PID, 
        window title, and process name using X11.

        Returns:
            Dict or None: Window information or None if no active window.
        """
        try:
            d = self.display.Display()
            root = d.screen().root

            # Get the active window ID
            active_window_property = root.get_full_property(
                d.intern_atom('_NET_ACTIVE_WINDOW'), self.X.AnyPropertyType
            )

            if not active_window_property:
                return None

            active_window_id = active_window_property.value[0]

            # No active window
            if active_window_id == 0:
                return None

            # Get the window object
            window_obj = d.create_resource_object('window', active_window_id)

            # Get window title
            window_name_property = window_obj.get_full_property(
                d.intern_atom('_NET_WM_NAME'), 0
            )

            window_title = "Unnamed window"
            if window_name_property:
                window_title = window_name_property.value.decode()

            # Get PID associated with window
            pid_property = window_obj.get_full_property(
                d.intern_atom('_NET_WM_PID'), 0
            )

            pid = None
            process_name = "Unknown"

            if pid_property:
                pid = pid_property.value[0]
                try:
                    process = psutil.Process(pid)
                    process_name = process.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    self.console_logger.debug(
                        f"Could not access process with PID {pid}")

            return {
                "pid": pid,
                "name": process_name,
                "title": window_title
            }

        except Exception as e:
            self.console_logger.debug(
                f"Error getting active window info: {str(e)}")
            return None

    def read_exe_path_for_pid(self, pid):
        process = psutil.Process(pid)
        exe_path = process.exe()  # works on Linux t
        return exe_path

    def _read_active_window_name_ubuntu(self) -> str:
        """
        Legacy method for compatibility. Gets just the window title.

        Returns:
            str: The title of the active window or an error message.
        """
        window_info = self._get_active_window_info()
        return window_info["title"] if window_info else "Unknown window"

    def _get_active_window_ubuntu(self) -> Optional[Dict]:
        """
        Legacy method for compatibility. Gets basic window process info.

        Returns:
            Dict or None: Basic process information or None.
        """
        window_info = self._get_active_window_info()
        if window_info:
            return {"pid": window_info["pid"], "name": window_info["name"]}
        return None

    def setup_window_hook(self) -> Generator[ProgramSessionDict, None, None]:
        """
        X11 implementation using event hooks for efficient window change detection.
        This method sets up an X11 event mask that triggers on window focus changes.

        Yields:
            Dict: Information about the new active window after each focus change.
        """
        # Select events on the root window
        self.root.change_attributes(event_mask=X.PropertyChangeMask)

        # Get atoms we need to watch
        net_active_window = self.display.intern_atom('_NET_ACTIVE_WINDOW')

        while True:
            event = self.display.next_event()

            # Check if it's a property change event on the root window
            if (event.type == X.PropertyNotify and
                event.window == self.root and
                    event.atom == net_active_window):

                window_info = self._read_x11()
                print(
                    f"Window changed: {window_info['window_title']} ({window_info['process_name']})")
                yield window_info
