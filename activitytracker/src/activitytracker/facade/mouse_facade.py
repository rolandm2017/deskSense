# type: ignore


from collections import deque

from datetime import datetime

from typing import TypedDict, List

from activitytracker.util.detect_os import OperatingSystemInfo
from activitytracker.object.classes import MouseEvent

from .monitoring import FacadeMonitoring

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
            # TODO: Just send a datetime.timestamp() since that's what will happen later
            event_dict = {"start": event["start"], "end": event["end"]}
            self.add_event(event_dict)

    def add_event(self, event: MouseEvent):
        self.queue.append(event)

    def read_event(self):
        if not hasattr(self, "monitoring"):
            self.monitoring = FacadeMonitoring("Mouse")

        queue_length = len(self.queue)
        self.monitoring.record_queue_length(queue_length)

        if self.queue:
            return self.queue.popleft()  # O(1) operation
        return None

    def get_all_events(self) -> List[MouseEvent]:
        all_events = list(self.queue)
        self.queue.clear()
        return all_events
