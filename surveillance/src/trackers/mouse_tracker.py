
# if os_type.startswith("Windows"):
#     # Windows
    
# if os_type.startswith("Ubuntu"):
#     # Linux
    


from enum import Enum, auto
from datetime import datetime
import csv
from pathlib import Path
import threading
import time


from ..util.detect_os import OperatingSystemInfo
from ..console_logger import ConsoleLogger
from ..facade.mouse_facade import MouseApiFacade, UbuntuMouseApiFacade, WindowsMouseApiFacade

class MouseEvent(str, Enum):
    START = "start"
    STOP = "stop"
    MOVE = "move"

class MouseTracker:
    def __init__(self, data_dir, mouse_api_facade, end_program_routine=None):
        """
        Initialize the MouseTracker with Windows event hooks.

        Note that the program starts when the Tracker object is initialized.
        
        Args:
            data_dir (Path): Directory where tracking data will be stored
        """
        self.mouse_facade: MouseApiFacade = mouse_api_facade
        self.data_dir = data_dir
        self.end_program_func = end_program_routine

        self.environment = OperatingSystemInfo()

        if self.environment.is_ubuntu:
            target_hook = self._start_hook_ubuntu
        elif self.environment.is_windows:
            target_hook = self._start_hook_windows
        else:
            print(self.environment)
            raise ValueError("Neither OS detected")

        self.movement_start = None
        self.last_position = None
        self.is_moving = False
        self.console_logger = ConsoleLogger()

        # Store session data to report on intervals
        self.session_data = []
        
        # Create an event to safely stop the listener thread
        self.stop_event = threading.Event()
        
        # Start mouse hook in a separate thread
        self.hook_thread = threading.Thread(target=target_hook)
        self.hook_thread.daemon = True
        self.hook_thread.start()


    def _start_hook_ubuntu(self):
        """Start the X11 mouse hook."""
        from Xlib import display, X
        from Xlib.ext import record
        from Xlib.protocol import rq
        # Get the display and create recording context
        self.display = display.Display()
        self.ctx = self.display.record_create_context(
            0,
            [record.AllClients],
            [{
                'core_requests': (0, 0),
                'core_replies': (0, 0),
                'ext_requests': (0, 0, 0, 0),
                'ext_replies': (0, 0, 0, 0),
                'delivered_events': (0, 0),
                'device_events': (X.MotionNotify, X.MotionNotify),
                'errors': (0, 0),
                'client_started': False,
                'client_died': False,
            }]
        )
        def callback(reply):
            """Handle X11 events."""
            if reply.category != record.FromServer:
                return
            
            if reply.client_swapped:
                return

            if not len(reply.data) or reply.data[0] < 2:
                return

            data = reply.data
            while len(data):
                event, data = rq.EventField(None).parse_binary_value(
                    data, self.display.display, None, None)
                
                if event.type == X.MotionNotify:
                    self._handle_mouse_move()

        # Enable recording context and start processing events
        self.display.record_enable_context(self.ctx, callback)
        
        # Keep processing events until stop_event is set
        while not self.stop_event.is_set():
            # Process X events
            self.display.process_events()
        
        # Clean up
        self.display.record_free_context(self.ctx)
        self.display.close()

    def _start_hook_windows(self):
        """Start the Windows mouse hook."""
        import win32con
        import ctypes
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
        msg = ctypes.wintypes.MSG()
        while not self.stop_event.is_set():
            if ctypes.windll.user32.PeekMessageA(ctypes.byref(msg), None, 0, 0, win32con.PM_REMOVE):
                ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                ctypes.windll.user32.DispatchMessageA(ctypes.byref(msg))
                
        # Clean up
        ctypes.windll.user32.UnhookWindowsHookEx(hook)

    def _handle_mouse_move(self):
        """Handle mouse movement events."""
        current_position = self.mouse_facade.get_cursor_pos()
        print(current_position, '168rm')
        
        if not self.is_moving:
            # Movement just started
            self.is_moving = True
            self.movement_start = datetime.now()
            self.last_position = current_position
            self._log_movement_to_csv(MouseEvent.START, current_position)
            self.console_logger.log_mouse_move(current_position)
            
            # Start a timer to detect when movement stops
            threading.Timer(0.1, self._check_if_stopped).start()
    
    def _check_if_stopped(self):
        """Check if mouse has stopped moving."""
        if self.is_moving:
            current_position = self.mouse_facade.get_cursor_pos()
            if current_position == self.last_position:
                # Mouse has stopped
                self.is_moving = False
                self._log_movement_to_csv(MouseEvent.STOP, current_position)
            else:
                # Mouse is still moving, check again
                self.last_position = current_position
                threading.Timer(0.1, self._check_if_stopped).start()

    def _log_movement_to_csv(self, event_type, position):
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
            file_path.parent.mkdir(parents=True, exist_ok=True)  # Create directories if needed
            with open(file_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['timestamp', 'event_type', 'x_position', 'y_position'])
                writer.writeheader()
        
        # Log the event
        event = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'x_position': position[0],
                'y_position': position[1]
            }
        with open(file_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'event_type', 'x_position', 'y_position'])
            writer.writerow(event)

        self.session_data.append(event)

    def gather_session(self):
        current = self.session_data
        self.session_data = self.preserve_open_events(current)  # todo: make currently open mouse movements not be reported, move them to the next interval
        return current
    
    def preserve_open_events(self, current_batch):
        # There can be one or zero open events, not 2.
        to_preserve = []
        if current_batch:
            if current_batch[-1]["event_type"] == MouseEvent.START:
                to_preserve.append(current_batch[-1])
        return to_preserve
        
    def stop(self):
        """Stop the mouse tracker and clean up."""
        self.stop_event.set()
        if self.end_program_func:
            print("here 240rm")
            self.end_program_func(self.generate_movement_report())
        if self.hook_thread.is_alive():
            print("here 243rm")
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
    


def end_program_readout(report):
    # prints the generated report
    print(report)


if __name__ == "__main__":
    os_type = OperatingSystemInfo()
    if os_type.is_ubuntu:
        facade_type = UbuntuMouseApiFacade
    elif os_type.is_windows:
        facade_type = WindowsMouseApiFacade
    api_facade = facade_type()
    folder = Path("/tmp")

        
    try:
        instance = MouseTracker(folder, api_facade, end_program_readout)
        # Add a way to keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        instance.stop()
        # Give the thread time to clean up
        time.sleep(0.5)
