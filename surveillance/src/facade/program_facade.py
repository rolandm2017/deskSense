import traceback
import psutil
from typing import Dict, Optional
from datetime import datetime
import platform

class ProgramApiFacade:
    def __init__(self, os):
        self.is_windows = os.is_windows
        self.is_ubuntu: os.is_ubuntu
        self.Xlib = None
        self.display = None
        self.X = None
        if self.is_windows:
            import win32gui
            import win32process
            self.win32gui = win32gui
            self.win32process = win32process
        else:
            # from Xlib import X, display
            from Xlib import display, X
            self.display = display
            self.X = X

    def read_current_program_info(self) -> Dict:
        if self.is_windows:
            return self._read_windows()
        return self._read_ubuntu()
    
    def _read_windows(self) -> Dict:
        window = self.win32gui.GetForegroundWindow()
        pid = self.win32process.GetWindowThreadProcessId(window)[1]
        process = psutil.Process(pid)
        return {
            "os": "Windows",
            "pid": pid,
            "process_name": process.name(),
            "window_title": self.win32gui.GetWindowText(window)
        }

    def listen_for_window_changes(self):
        d = self.display.Display()
        root = d.screen().root
        
        # Listen for focus change events
        root.change_attributes(event_mask=self.X.FocusChangeMask | self.X.PropertyChangeMask)
        
        while True:
            event = d.next_event()
            if event.type == self.X.PropertyNotify:
                if event.atom == d.intern_atom('_NET_ACTIVE_WINDOW'):
                    # Window focus changed - get new window info
                    window_info = self._read_ubuntu()
                    yield window_info

    def _read_ubuntu(self) -> Dict:
        # Ubuntu implementation using wmctrl or xdotool could go here
        # For now, returning active process info
        active = self._get_active_window_ubuntu()
        window_name = self._read_active_window_name_ubuntu()
        print(active,'61vv')
        print(window_name,'62vv')
        return {
            "os": "Ubuntu",
            "pid": active["pid"] if active else None,
            "process_name": active["name"] if active else None,
            "window_title": window_name
        }
    
    def _read_active_window_name_ubuntu(self):
        try:
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
                return window_name.value
            else:
                return "Unnamed window"
        except Exception as e:
            # <class 'Xlib.error.BadWindow'>: 
            #     code = 3, resource_id = <Resource 0x00000000>, 
            #     sequence_number = 22, major_opcode = 20, minor_opcode = 0 []
            # print(e) 
            # print(traceback.format_exc())
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