import psutil
from Xlib import display, X
from Xlib.error import BadWindow

from typing import Dict, Optional, Generator

from .program_facade_base import ProgramFacadeInterface

from surveillance.src.object.classes import ProgramSessionDict
from surveillance.src.util.console_logger import ConsoleLogger


class UbuntuProgramFacadeCore(ProgramFacadeInterface):
    def __init__(self):
        self.console_logger = ConsoleLogger()
        self.Xlib = None
        self.display = display
        self.X = X

    def listen_for_window_changes(self) -> Generator[ProgramSessionDict, None, None]:
        if self.X is None or self.display is None:
            raise AttributeError(
                "Crucial component was not initialized")

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
                    window_info = self._read_ubuntu()
                    yield window_info

    def _read_ubuntu(self) -> ProgramSessionDict:
        # Ubuntu implementation using wmctrl or xdotool could go here
        # For now, returning active process info
        active = self._get_active_window_ubuntu()
        window_name = self._read_active_window_name_ubuntu()

        process_name: str = active["process_name"] if active else "Unknown"
        exe_path: str = active["exe_path"] if active else "Unknown"

        #         process = psutil.Process(pid)
        # exe_path = process.exe()  # This gets the full path to the executable
        # process_name = process.name()

        return {
            "os": "Ubuntu",
            "exe_path": exe_path,
            "pid": active["pid"] if active else None,
            "process_name": process_name,
            "window_title": window_name  # window_title with the detail
        }

    def _get_active_window_id(self, root, initialized_display):
        return root.get_full_property(
            initialized_display.intern_atom(
                '_NET_ACTIVE_WINDOW'), self.X.AnyPropertyType
        ).value[0]

    def _read_active_window_name_ubuntu(self):
        """Returns the program title like what you'd see during alt-tab."""
        try:
            if self.X is None or self.display is None:
                raise AttributeError(
                    "Crucial component was not initialized")

            # Connect to the X server
            d = self.display.Display()
            root = d.screen().root

            # Get the active window ID
            active_window_id = self._get_active_window_id(root, d)

            # Get the window object
            window_obj = d.create_resource_object('window', active_window_id)
            window_name = window_obj.get_full_property(
                d.intern_atom('_NET_WM_NAME'), 0
            )

            if window_name:
                # convert bytestring -> plain string as soon as it enters the system. don't let it leave the facade
                window_name_as_string = window_name.value.decode()
                return window_name_as_string  # might need to specify encoding
            else:
                return "Unnamed window"

        except BadWindow as e:
            # Handle specifically BadWindow errors
            self.console_logger.log_yellow(f"BadWindow error occurred: {e}")
            return "Alt-tab window"
        except Exception as e:
            # Handle other exceptions
            self.console_logger.log_yellow(
                f"Unexpected error getting active window: {e}")
            return "Unknown"

    def _get_active_window_ubuntu(self) -> Optional[Dict]:
        try:
            # Connect to X server to get active window
            d = self.display.Display()
            root = d.screen().root

            # Get active window ID
            active_window_id = self._get_active_window_id(root, d)

            # Get window PID using _NET_WM_PID property
            window_obj = d.create_resource_object('window', active_window_id)
            pid = window_obj.get_full_property(
                d.intern_atom('_NET_WM_PID'), self.X.AnyPropertyType
            )

            window_name = window_obj.get_full_property(
                d.intern_atom('_NET_WM_NAME'), 0
            )

            if pid:
                # Get process info using psutil with the specific PID
                pid_value = pid.value[0]
                process = psutil.Process(pid_value)
                return {
                    "window_title":  window_name,
                    "pid": pid_value,
                    "process_name": process.name(),
                    "exe_path": process.exe()
                }
            return None
        except BadWindow as e:
            return {
                "window_title": "Alt-tab window",
                "pid": 0,
                "process_name": "Alt-tab",
                "exe_path": "Unknown"
            }
        except Exception as e:
            self.console_logger.debug(f"Error getting active window: {e}")
            return None

    # def _get_active_window_ubuntu(self) -> Optional[Dict]:
    #     for process in psutil.process_iter(['pid', 'name']):
    #         try:
    #             if process.status() == 'running':
    #                 return {"pid": process.pid, "process_name": process.name(), "exe_path": process.exe()}
    #         except (psutil.NoSuchProcess, psutil.AccessDenied):
    #             continue
    #     return None

    def setup_window_hook(self):
        """
        X11 implementation using event hooks for efficient window change detection.
        This method sets up an X11 event mask that triggers on window focus changes.

        Yields:
            Dict: Information about the new active window after each focus change.
        """
        pass  # Note that the implementation exists in git
