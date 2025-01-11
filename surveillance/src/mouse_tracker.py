
import win32api
import win32gui
import win32con
from datetime import datetime
import csv
from pathlib import Path
import threading
import ctypes
from ctypes import wintypes

class MouseTracker:
    def __init__(self, data_dir):
        """
        Initialize the MouseTracker with Windows event hooks.
        
        Args:
            data_dir (Path): Directory where tracking data will be stored
        """
        self.data_dir = data_dir
        self.movement_start = None
        self.last_position = None
        self.is_moving = False
        
        # Create an event to safely stop the listener thread
        self.stop_event = threading.Event()
        
        # Start mouse hook in a separate thread
        self.hook_thread = threading.Thread(target=self._start_hook)
        self.hook_thread.daemon = True
        self.hook_thread.start()

    def _start_hook(self):
        """Start the Windows mouse hook."""
        # Define the mouse hook callback
        def mouse_callback(nCode, wParam, lParam):
            """
            Callback function for mouse events.
            Called by Windows whenever there's mouse movement.
            """
            if nCode >= 0:  # "if allowed to process the event"
                if wParam == win32con.WM_MOUSEMOVE:  # "if is a mouse move event"
                    self._handle_mouse_move()
                    
            # Call the next hook
            return ctypes.windll.user32.CallNextHookEx(None, nCode, wParam, ctypes.py_object(lParam))
        
        # Convert the callback function to a C-callable function
        CMPFUNC = ctypes.WINFUNCTYPE(
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)
        )
        pointer = CMPFUNC(mouse_callback)
        
        # Set up the mouse hook
        hook = ctypes.windll.user32.SetWindowsHookExA(
            win32con.WH_MOUSE_LL,
            pointer,
            None,  # For LowLevel hooks, this parameter is ignored and should be None
            0
        )
        
        if not hook:
            raise Exception('Failed to set mouse hook')
        
        # Message loop to keep the hook active
        msg = wintypes.MSG()
        while not self.stop_event.is_set():
            if ctypes.windll.user32.PeekMessageA(ctypes.byref(msg), None, 0, 0, win32con.PM_REMOVE):
                ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                ctypes.windll.user32.DispatchMessageA(ctypes.byref(msg))
                
        # Clean up
        ctypes.windll.user32.UnhookWindowsHookEx(hook)

    def _handle_mouse_move(self):
        """Handle mouse movement events."""
        current_position = win32api.GetCursorPos()
        
        if not self.is_moving:
            # Movement just started
            self.is_moving = True
            self.movement_start = datetime.now()
            self.last_position = current_position
            self._log_movement('start', current_position)
            
            # Start a timer to detect when movement stops
            threading.Timer(0.1, self._check_if_stopped).start()
    
    def _check_if_stopped(self):
        """Check if mouse has stopped moving."""
        if self.is_moving:
            current_position = win32api.GetCursorPos()
            if current_position == self.last_position:
                # Mouse has stopped
                self.is_moving = False
                self._log_movement('stop', current_position)
            else:
                # Mouse is still moving, check again
                self.last_position = current_position
                threading.Timer(0.1, self._check_if_stopped).start()

    def _log_movement(self, event_type, position):
        """
        Log mouse movement events to CSV.
        
        Args:
            event_type (str): Either 'start' or 'stop'
            position (tuple): (x, y) coordinates of mouse position
        """
        date_str = datetime.now().strftime('%Y-%m-%d')
        file_path = self.data_dir / f'mouse_tracking_{date_str}.csv'
        
        # Create file with headers if it doesn't exist
        if not file_path.exists():
            with open(file_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['timestamp', 'event_type', 'x_position', 'y_position'])
                writer.writeheader()
        
        # Log the event
        with open(file_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'event_type', 'x_position', 'y_position'])
            writer.writerow({
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'x_position': position[0],
                'y_position': position[1]
            })

    def stop(self):
        """Stop the mouse tracker and clean up."""
        self.stop_event.set()
        if self.hook_thread.is_alive():
            self.hook_thread.join()

    def generate_movement_report(self, date_str=None):
        """
        Generate a report of mouse movement patterns for a specific date.
        
        Args:
            date_str (str): Date in format 'YYYY-MM-DD'. If None, uses current date.
        
        Returns:
            dict: Report containing movement statistics
        """
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
            
        file_path = self.data_dir / f'mouse_tracking_{date_str}.csv'
        if not file_path.exists():
            return "No mouse tracking data available for this date."
            
        movement_sessions = []
        start_time = None
        
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['event_type'] == 'start':
                    start_time = datetime.fromisoformat(row['timestamp'])
                elif row['event_type'] == 'stop' and start_time:
                    end_time = datetime.fromisoformat(row['timestamp'])
                    duration = (end_time - start_time).total_seconds()
                    movement_sessions.append(duration)
                    start_time = None
        
        if not movement_sessions:
            return {
                'date': date_str,
                'total_movements': 0,
                'avg_movement_duration': 0,
                'total_movement_time': 0
            }
            
        return {
            'date': date_str,
            'total_movements': len(movement_sessions),
            'avg_movement_duration': round(sum(movement_sessions) / len(movement_sessions), 2),
            'total_movement_time': round(sum(movement_sessions), 2)
        }