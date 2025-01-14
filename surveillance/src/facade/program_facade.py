import psutil
from typing import Dict, Optional
import platform

class ProgramApiFacade:
    def __init__(self, os):
        self.is_windows = os.is_windows
        if self.is_windows:
            import win32gui
            import win32process
            self.win32gui = win32gui
            self.win32process = win32process
        

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
        return {
            "os": "ubuntu",
            "pid": active["pid"] if active else None,
            "process_name": active["name"] if active else None,
            "window_title": None  # Would need wmctrl/xdotool for this
        }

    def _get_active_window_ubuntu(self) -> Optional[Dict]:
        # Basic implementation - could be enhanced with window manager tools
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.status() == 'running':
                    return {"pid": proc.pid, "name": proc.name()}
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None