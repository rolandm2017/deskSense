# classes.py
# For various classes
from datetime import datetime, timedelta
from typing import TypedDict, Optional


class ChromeSessionData:
    domain: str
    detail: str
    start_time: Optional[datetime]  # UTC timestamps
    end_time: Optional[datetime]  # UTC timestamps
    duration: Optional[timedelta]
    productive: bool

    def __init__(self, domain, detail, start_time, end_time=None, productive=False, duration_for_tests=None):
        self.domain = domain
        self.detail = detail
        self.start_time = start_time
        self.end_time = end_time
        if duration_for_tests:
            self.duration = duration_for_tests
        else:
            self.duration = None
        self.productive = productive

    @staticmethod
    def parse_time_string(time_str):
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_parts = parts[2].split('.')
        seconds = int(seconds_parts[0])
        microseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
        
        return timedelta(
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            microseconds=microseconds
        )

    def __str__(self):
        end_time = self.end_time if self.end_time else "tbd"
        return f"ChromeSessionData(domain='{self.domain}', detail='{self.detail}', \n\tstart_time={self.start_time}, \n\tend_time={end_time}, duration={self.duration}, productive={self.productive})"


class ProgramSessionData:
    window_title: str
    detail: str
    start_time: Optional[datetime]  # UTC timestamps
    end_time: Optional[datetime]  # UTC timestamps
    duration: Optional[timedelta]
    productive: bool

    def __init__(self, title="", detail="", start_time=None, end_time=None, productive=False, duration_for_tests=None):
        """Only use duration in testing. Don't use it otherwise. 'duration_for_tests' exists only for e2e tests thresholds"""
        self.window_title = title
        self.detail = detail
        self.start_time = start_time
        self.end_time = end_time
        if start_time and end_time:
            # if isinstance(start_time, str) and isinstance(end_time, str):
            #     start = datetime.fromisoformat(start_time)
            #     end = datetime.fromisoformat(end_time)
            #     self.duration = end - start
            # else:
            self.duration = end_time - start_time
        else:
            if duration_for_tests:
                self.duration = duration_for_tests
            else:
                self.duration = None
        self.productive = productive

    def parse_time_string(self, time_str):
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_parts = parts[2].split('.')
        seconds = int(seconds_parts[0])
        microseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
        
        return timedelta(
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            microseconds=microseconds
        )

    def __str__(self):
        end_time = self.end_time if self.end_time else "tbd"
        return f"ProgramSessionData(window_title='{self.window_title}', detail='{self.detail}', \n\tstart_time={self.start_time}, \n\tend_time={end_time}, duration={self.duration}, productive={self.productive})"


class MouseEvent(TypedDict):
    start: float
    end: float


class PeripheralAggregate:
    """
    Base class for all peripheral aggregates.
    A deliverable that becomes a database entry.

    This is the finished package template.
    """

    def __init__(self, start_time, end_time, count_of_events=None):
        self.start_time = start_time
        self.end_time = end_time
        self.count = count_of_events

    def __str__(self):
        return f"Peripheral aggregate from {self.start_time} to {self.end_time} with {self.count} events"


class KeyboardAggregate(PeripheralAggregate):
    """
    Keyboard-specific implementation of PeripheralAggregate.
    """

    def __str__(self):
        return f"Keyboard aggregate from {self.start_time} to {self.end_time} with {self.count} events"


class MouseAggregate(PeripheralAggregate):
    """
    Mouse-specific implementation of PeripheralAggregate.
    """

    def __str__(self):
        return f"Mouse aggregate from {self.start_time} to {self.end_time} with {self.count} events"


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
            return f"Mouse movement from {self.start_time} to {self.end_time} - {self.source}"
        return f"Mouse movement from {self.start_time} to {self.end_time} : nameless"
