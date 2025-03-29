
from collections import deque

from datetime import datetime

from .monitoring import FacadeMonitoring


class KeyboardFacadeCore:
    def __init__(self):
        self.queue = deque()

    def handle_keyboard_message(self, event):
        """Handle keyboard events from the message receiver."""
        if "timestamp" in event:
            # TODO: Just send the timestamp on the Recorder side
            self.add_event(event["timestamp"])

    def add_event(self, time: float):
        """It really does need to be a timestamp, because later, the EventAggregator compares timestamps.`"""
        self.queue.append(time)

    def read_event(self):
        if not hasattr(self, 'monitoring'):
            self.monitoring = FacadeMonitoring("Keyboard")

        queue_length = len(self.queue)
        self.monitoring.record_queue_length(queue_length)

        if self.queue:
            return self.queue.popleft()  # O(1) operation
        return None

    def event_type_is_key_down(self, event):
        return event is not None  # If event exists, it was a key press

    def get_all_events(self):
        all_events = list(self.queue)
        self.queue.clear()
        return all_events
