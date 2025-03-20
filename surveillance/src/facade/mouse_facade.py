# type: ignore


from collections import deque

from datetime import datetime

from typing import TypedDict

from ..util.detect_os import OperatingSystemInfo
from ..object.classes import MouseCoords

os_type = OperatingSystemInfo()
if os_type.is_windows:
    from win32api import GetCursorPos
if os_type.is_ubuntu:
    from Xlib import display


class MouseEvent(TypedDict):
    start: str  # or datetime, float, etc. depending on your needs
    end: str    # same type as start


class MouseFacadeCore:
    def __init__(self):
        self.queue = deque()

    def handle_mouse_message(self, event):
        """Handle mouse events from the message receiver."""
        if "start" in event and "end" in event:
            print(event, "in mouse facade core 34ru")
            event_dict = {
                "start": datetime.fromisoformat(event["start"]),
                "end": datetime.fromisoformat(event["end"])
            }
            self.add_event(event_dict)

    def add_event(self, event: MouseEvent):
        self.queue.append(event)

    def read_event(self):
        if self.queue:
            return self.queue.popleft()  # O(1) operation
        return None


# class WindowsMouseApiFacade:
#     def __init__(self):
#         pass

#     def _start_hook_windows(self):
#         """Start the Windows mouse hook."""
#         import win32con
#         import ctypes
#         # Define the mouse hook callback

#         def mouse_callback(nCode, wParam, lParam):
#             """
#             Callback function for mouse events.
#             Called by Windows whenever there's mouse movement.
#             """
#             if nCode >= 0:  # "if allowed to process the event"
#                 if wParam == win32con.WM_MOUSEMOVE:  # "if is a mouse move event"
#                     self._handle_mouse_move()

#             # Call the next hook
#             return ctypes.windll.user32.CallNextHookEx(None, nCode, wParam, ctypes.py_object(lParam))

#         # Convert the callback function to a C-callable function
#         CMPFUNC = ctypes.WINFUNCTYPE(
#             ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(
#                 ctypes.c_void_p)
#         )
#         pointer = CMPFUNC(mouse_callback)

#         # Set up the mouse hook
#         hook = ctypes.windll.user32.SetWindowsHookExA(
#             win32con.WH_MOUSE_LL,
#             pointer,
#             None,  # For LowLevel hooks, this parameter is ignored and should be None
#             0
#         )

#         if not hook:
#             raise Exception('Failed to set mouse hook')

#         # Message loop to keep the hook active
#         msg = ctypes.wintypes.MSG()
#         while not self.stop_event.is_set():
#             if ctypes.windll.user32.PeekMessageA(ctypes.byref(msg), None, 0, 0, win32con.PM_REMOVE):
#                 ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
#                 ctypes.windll.user32.DispatchMessageA(ctypes.byref(msg))

#         # Clean up
#         ctypes.windll.user32.UnhookWindowsHookEx(hook)


# class UbuntuMouseApiFacadeCore:
#     def __init__(self):
#         from Xlib import display
#         self.current_position = (0, 0)
#         self.display = display.Display()

#     def get_position_coords(self):
#         """Single position check from X11"""
#         query = self.display.screen().root.query_pointer()
#         return MouseCoords(query.root_x, query.root_y)
