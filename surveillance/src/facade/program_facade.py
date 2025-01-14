import psutil
from typing import Dict, Optional
from datetime import datetime
import platform

class ProgramApiFacade:
    def __init__(self, os):
        self.is_windows = os.is_windows
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
            "os": "windows",
            "pid": pid,
            "process_name": process.name(),
            "window_title": self.win32gui.GetWindowText(window)
        }

    def _read_ubuntu(self) -> Dict:
        # Ubuntu implementation using wmctrl or xdotool could go here
        # For now, returning active process info
        active = self._get_active_window_ubuntu()
        print(self.read_active_window(), '41vv')
        return {
            "os": "ubuntu",
            "pid": active["pid"] if active else None,
            "process_name": active["name"] if active else None,
            "window_title": None  # Would need wmctrl/xdotool for this
        }
    
    def read_active_window(self):
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
            print(e.__traceback__)
            return f"Error: {str(e)}"

    def _get_active_window_ubuntu(self) -> Optional[Dict]:
        # Basic implementation - could be enhanced with window manager tools
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.status() == 'running':
                    return {"pid": proc.pid, "name": proc.name()}
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None