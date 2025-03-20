# type: ignore


from collections import deque

from datetime import datetime

from typing import TypedDict, List

from ..util.detect_os import OperatingSystemInfo
from ..object.classes import MouseCoords, MouseEvent

os_type = OperatingSystemInfo()
if os_type.is_windows:
    from win32api import GetCursorPos
if os_type.is_ubuntu:
    from Xlib import display


class MouseFacadeCore:
    def __init__(self):
        self.queue = deque()

    async def handle_mouse_message(self, event):
        """Handle mouse events from the message receiver."""
        if "start" in event and "end" in event:
            print(event, "in mouse facade core 34ru")
            # TODO: Just send a datetime.timestamp() since that's what will happen later
            event_dict = {
                "start": event["start"],
                "end": event["end"]
            }
            self.add_event(event_dict)

    def add_event(self, event: MouseEvent):
        self.queue.append(event)

    def read_event(self):
        if self.queue:
            return self.queue.popleft()  # O(1) operation
        return None

    def get_all_events(self) -> List[MouseEvent]:
        all_events = list(self.queue)
        self.queue.clear()
        return all_events
