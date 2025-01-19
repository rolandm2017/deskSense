# classes.py
# For various classes


class KeyboardAggregateDatabaseEntryDeliverable:
    def __init__(self, session_start_time, session_end_time):
        self.session_start_time = session_start_time
        self.session_end_time = session_end_time

    def __str__(self):
        return f"Keyboard session from {self.session_start_time} to {self.session_end_time}"


class MouseCoords:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.timestamp = None


class MouseMovementEvent:
    def __init__(self, event_type, position, timestamp):
        self.event_type = event_type
        self.position = position
        self.timestamp = timestamp

class MouseMoveWindow:
    def __init__(self, start_of_window, end_of_window):
        """Where the mouse was is irrelevant. From when to when it was moving is the important part."""
        self.start_time = start_of_window
        self.end_time = end_of_window

    def __str__(self):
        return f"Mouse movement from {self.start_time} to {self.end_time}"
