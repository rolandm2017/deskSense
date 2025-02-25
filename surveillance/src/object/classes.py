# classes.py
# For various classes
from datetime import datetime, timedelta
from typing import TypedDict, Optional


class ChromeSessionData:
    domain: str
    detail: str
    start_time: datetime  # UTC timestamps
    end_time: datetime  # UTC timestamps
    duration: Optional[timedelta]
    productive: bool

    def __init__(self):
        self.domain = ""
        self.detail = ""
        self.start_time = None
        self.duration = None
        self.productive = None

    def __str__(self):
        return f"ChromeSessionData(domain='{self.domain}', detail='{self.detail}', \n\tstart_time={self.start_time}, \n\tend_time={self.end_time}, duration={self.duration}, productive={self.productive})"


class ProgramSessionData:
    window_title: str
    detail: str
    start_time: datetime  # UTC timestamps
    end_time: datetime  # UTC timestamps
    duration: timedelta
    productive: bool

    def __init__(self):
        self.window_title = ""
        self.detail = ""
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.productive = None

    def __str__(self):
        return f"ProgramSessionData(window_title='{self.window_title}', detail='{self.detail}', \n\tstart_time={self.start_time}, \n\tend_time={self.end_time}, duration={self.duration}, productive={self.productive})"


class KeyboardAggregate:
    """
    A deliverable that becomes a database entry.

    This is the FINISHED package.
    """

    def __init__(self, session_start_time, session_end_time, count_of_events=None):
        self.session_start_time = session_start_time
        self.session_end_time = session_end_time
        self.count = count_of_events

    def __str__(self):
        return f"Keyboard aggregate from {self.session_start_time} to {self.session_end_time}"


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
    def __init__(self, start_of_window, end_of_window, source=None):
        """Where the mouse was is irrelevant. From when to when it was moving is the important part."""
        self.start_time = start_of_window
        self.end_time = end_of_window
        self.source = source

    def __str__(self):
        if self.source:
            return f"Mouse movement from {self.start_time} to {self.end_time} - {self.source} - {str(self.count)}"
        return f"Mouse movement from {self.start_time} to {self.end_time} : nameless"
