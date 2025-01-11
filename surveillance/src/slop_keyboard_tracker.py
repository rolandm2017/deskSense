import win32api
import win32con
import win32gui
import ctypes
import threading
import time
from datetime import datetime
import csv
from pathlib import Path

class KeyActivityTracker:
    def __init__(self, data_dir):
        """Initialize the key activity tracker.
        
        Args:
            data_dir (Path): Directory to store the activity data
        """
        self.data_dir = data_dir
        self.running = False
        self.press_count = 0
        self.last_save_time = datetime.now()
        self.lock = threading.Lock()
        self.hook = None
        
    def _save_data(self):
        """Save the current press count to a CSV file."""
        if self.press_count == 0:
            return
            
        date_str = datetime.now().strftime('%Y-%m-%d')
        file_path = self.data_dir / f'keyboard_activity_{date_str}.csv'
        
        # Create file with headers if it doesn't exist
        if not file_path.exists():
            with open(file_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['timestamp', 'press_count'])
                writer.writeheader()
        
        current_time = datetime.now()
        
        # Save the data
        with open(file_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'press_count'])
            writer.writerow({
                'timestamp': current_time.isoformat(),
                'press_count': self.press_count
            })
            
        # Reset counter after saving
        with self.lock:
            self.press_count = 0
            self.last_save_time = current_time

    @staticmethod
    def _keyboard_hook_proc(nCode, wParam, lParam):
        """Low level keyboard hook callback."""
        if nCode >= 0:
            # Only count key down events
            if wParam == win32con.WM_KEYDOWN:
                # Get instance through win32gui
                instance = win32gui.GetWindowLong(win32gui.GetForegroundWindow(), win32con.GWL_USERDATA)
                if instance:
                    tracker = ctypes.cast(instance, ctypes.py_object).value
                    with tracker.lock:
                        tracker.press_count += 1
                    
                    # Save data every minute
                    current_time = datetime.now()
                    if (current_time - tracker.last_save_time).total_seconds() >= 60:
                        tracker._save_data()

        # Call the next hook
        return ctypes.windll.user32.CallNextHookEx(None, nCode, wParam, lParam)

    def start(self):
        """Start tracking key activity."""
        if not self.running:
            self.running = True
            
            # Create a hidden window for instance storage
            wndclass = win32gui.WNDCLASS()
            wndclass.lpszClassName = 'KeyTrackerWindow'
            wndclass.lpfnWndProc = lambda h, m, w, l: win32gui.DefWindowProc(h, m, w, l)
            win32gui.RegisterClass(wndclass)
            self.hwnd = win32gui.CreateWindow(wndclass.lpszClassName, 
                                            '', 0, 0, 0, 0, 0, 0, 0, 0, None)
            win32gui.SetWindowLong(self.hwnd, win32con.GWL_USERDATA, id(self))
            
            # Convert callback to C function pointer
            CMPFUNC = ctypes.CFUNCTYPE(
                ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)
            )
            self.hook_pointer = CMPFUNC(self._keyboard_hook_proc)
            
            # Set up the low-level keyboard hook
            self.hook = ctypes.windll.user32.SetWindowsHookExA(
                win32con.WH_KEYBOARD_LL,
                self.hook_pointer,
                None,  # For WH_KEYBOARD_LL, hMod should be NULL
                0
            )
            
            if not self.hook:
                self.running = False
                raise Exception("Failed to install keyboard hook")
                
            # Start message pump in a separate thread
            self.pump_thread = threading.Thread(target=self._message_pump)
            self.pump_thread.daemon = True
            self.pump_thread.start()

    def _message_pump(self):
        """Run the message pump to process keyboard events."""
        while self.running:
            try:
                msg = ctypes.wintypes.MSG()
                if ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                    ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                    ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
            except Exception:
                continue
            time.sleep(0.1)

    def stop(self):
        """Stop tracking key activity and save final data."""
        if self.running:
            self.running = False
            if self.hook:
                ctypes.windll.user32.UnhookWindowsHookEx(self.hook)
                self.hook = None
            self._save_data()  # Save any remaining data
            if hasattr(self, 'hwnd'):
                win32gui.DestroyWindow(self.hwnd)

    def get_activity_report(self, date_str=None):
        """Generate an activity report for a specific date.
        
        Args:
            date_str (str): Date in YYYY-MM-DD format. Defaults to today.
            
        Returns:
            dict: Activity statistics for the specified date
        """
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
            
        file_path = self.data_dir / f'keyboard_activity_{date_str}.csv'
        if not file_path.exists():
            return {"date": date_str, "total_keypresses": 0, "active_minutes": 0}
            
        total_keypresses = 0
        active_minutes = 0
        
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_keypresses += int(row['press_count'])
                if int(row['press_count']) > 0:
                    active_minutes += 1
                    
        return {
            "date": date_str,
            "total_keypresses": total_keypresses,
            "active_minutes": active_minutes
        }
    

# FIXME: it became slow as hell