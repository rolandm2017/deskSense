from Xlib import display, X  # might have to cram into a ubuntu specific conditional import
from Xlib.ext import record  # might have to cram into a ubuntu specific conditional import
from Xlib.protocol import rq # might have to cram into a ubuntu specific conditional import

from ..util.detect_os import OperatingSystemInfo
os_type = OperatingSystemInfo()
if os_type.is_windows:
    from win32api import GetCursorPos
if os_type.is_ubuntu:
    from Xlib import display

class MouseApiFacade:
    def __init__(self, os_info):
        pass

    def get_cursor_pos(self):
        pass

class WindowsMouseApiFacade:
    def __init__(self):
        pass

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

some_dict = {
                'core_requests': (0, 0),
                'core_replies': (0, 0),
                'ext_requests': (0, 0, 0, 0),
                'ext_replies': (0, 0, 0, 0),
                'delivered_events': (0, 0),
                'device_events': (X.MotionNotify, X.MotionNotify),
                'errors': (0, 0),
                'client_started': False,
                'client_died': False,
            }



class MouseCoords:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timestamp = None

class UbuntuMouseApiFacadeCore:
    def __init__(self):
        from Xlib import display
        self.current_position = (0, 0)
        self.display = display.Display()

    def get_position_coords(self):
        """Single position check from X11"""
        query = self.display.screen().root.query_pointer()
        return MouseCoords(query.root_x, query.root_y)    

class UbuntuMouseApiFacade:
    def __init__(self):
        from Xlib import display
        from threading import Thread
        import time

        self.running = False
        self.current_position = (0, 0)
        self.thread = None

        self.display = display.Display()
        self.Thread = Thread
        self.sleep = time.sleep

    def _track_mouse(self):
        """Private method to continuously update the mouse position in a separate thread."""
        while self.running:
            query = self.display.screen().root.query_pointer()
            self.current_position = (query.root_x, query.root_y)
            self.sleep(0.1)  # Polling delay to reduce CPU usage

    def start(self):
        """Start tracking the mouse position in a separate thread."""
        if not self.running:
            self.running = True
            self.thread = self.Thread(target=self._track_mouse, daemon=True)
            self.thread.start()

    def stop(self):
        """Stop tracking the mouse position and clean up resources."""
        if self.running:
            self.running = False
            self.thread.join()

    def get_position(self):
        """Get the current mouse position as a tuple (x, y)."""
        return self.current_position

