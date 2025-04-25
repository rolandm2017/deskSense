import psutil
from Xlib import display, X

from typing import Dict, Optional, Generator, cast

from .program_facade_base import ProgramFacadeInterface

from surveillance.src.util.console_logger import ConsoleLogger
from surveillance.src.object.classes import ProgramSessionDict


class UbuntuProgramFacadeCore(ProgramFacadeInterface):
    def __init__(self):
        self.console_logger = ConsoleLogger()
        self.Xlib = None
        self.display = display
        self.X = X

    def read_current_program_info(self) -> ProgramSessionDict:
        return self._read_ubuntu()

    def read_exe_path_for_pid(self, pid):
        process = psutil.Process(pid)
        exe_path = process.exe()  # works on Linux t
        return exe_path

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
        active_process_name = cast(
            str, active["name"] if active else "Unknown")
        active_process_pid = cast(int, active["pid"] if active else 9999)
        exe_path = self.read_exe_path_for_pid(active_process_pid)
        window_name = self._read_active_window_name_ubuntu()
        # FIXME: "Program None - rlm@kingdom: ~/Code/deskSense/surveillance"
        return {
            "exe_path": exe_path,
            "os": "Ubuntu",
            "pid": active_process_pid,
            "process_name": active_process_name,
            "window_title": window_name  # window_title with the detail
        }

    def _read_active_window_name_ubuntu(self):
        try:
            if self.X is None or self.display is None:
                raise AttributeError(
                    "Crucial component was not initialized")

            # Connect to the X server
            d = self.display.Display()
            root = d.screen().root

            # Get the active window ID
            active_window_id = root.get_full_property(
                d.intern_atom('_NET_ACTIVE_WINDOW'), self.X.AnyPropertyType
            ).value[0]

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
        except Exception as e:
            # Will always be:
            # <class 'Xlib.error.BadWindow'>:
            #     code = 3, resource_id = <Resource 0x00000000>,
            #     sequence_number = 22, major_opcode = 20, minor_opcode = 0 []
            # TODO: ensure it's alt tab window
            return "Alt-tab window"  # "Alt-Tab Window (Most Likely)"

    def _get_active_window_ubuntu(self) -> Optional[Dict]:
        # Basic implementation - could be enhanced with window manager tools
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.status() == 'running':
                    return {"pid": proc.pid, "name": proc.name()}
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
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
