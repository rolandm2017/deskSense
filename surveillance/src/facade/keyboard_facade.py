
from collections import deque

from datetime import datetime


class KeyboardFacadeCore:
    def __init__(self):
        self.queue = deque()

    def handle_keyboard_message(self, event):
        """Handle keyboard events from the message receiver."""
        if "timestamp" in event:
            print(event, 'in keyboard facade 20ru')
            converted_datetime = datetime.fromisoformat(event["timestamp"])
            self.add_event(converted_datetime)

    def add_event(self, time: datetime):
        """It really does need to be a timestamp, because later, the EventAggregator compares timestamps.`"""
        self.queue.append(time.timestamp())

    def read_event(self):
        if self.queue:
            return self.queue.popleft()  # O(1) operation
        return None

    def event_type_is_key_down(self, event):
        # print(event, event is not None, "21vv")
        return event is not None  # If event exists, it was a key press
