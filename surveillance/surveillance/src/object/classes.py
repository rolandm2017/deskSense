# classes.py
# For various classes
from datetime import datetime, timedelta, timezone
from typing import TypedDict, Optional

from surveillance.src.util.time_wrappers import UserLocalTime


class ProgramSessionDict(TypedDict):
    os: str
    pid: int | None
    process_name: str
    exe_path: str
    window_title: str

class ProgramSession:
    exe_path: str
    process_name: str
    window_title: str
    detail: str
    start_time: UserLocalTime
    productive: bool

    def __init__(self, exe_path="", process_name="", window_title="", detail="", start_time=UserLocalTime(datetime(2000, 1, 1, tzinfo=timezone.utc)), productive=False):
        # IF you remove the default args for this class, then you will have to do A LOT of cleanup in the test data.
        self.exe_path = exe_path
        self.process_name = process_name
        self.window_title = window_title
        self.detail = detail
        self.start_time = start_time
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
        return f"ProgramSession(exe_path='{self.exe_path}', process_name='{self.process_name}', \n\ttitle='{self.window_title}', detail='{self.detail}', \n\tstart_time='{self.start_time}', \n\tproductive='{self.productive}')"


class CompletedProgramSession(ProgramSession):
    end_time: UserLocalTime
    duration: timedelta

    def __init__(
        self, 
        exe_path="", 
        process_name="", 
        window_title="", 
        detail="", 
        start_time=UserLocalTime(datetime(2000, 1, 1, tzinfo=timezone.utc)), 
        end_time=UserLocalTime(datetime(2000, 1, 1, tzinfo=timezone.utc)), 
        productive=False, 
        duration_for_tests=None
    ):
        """Only use duration arg in testing. Don't use it otherwise. 'duration_for_tests' exists only for e2e tests thresholds"""
        
        # Initialize the base class first
        super().__init__(
            exe_path=exe_path,
            process_name=process_name,
            window_title=window_title,
            detail=detail,
            start_time=start_time,
            productive=productive
        )
        
        # Add the fields specific to CompletedProgramSession
        self.end_time = end_time
        
        # Calculate duration
        if start_time and end_time:
            self.duration = end_time - start_time
        elif duration_for_tests:
            self.duration = duration_for_tests
        else:
            self.duration = timedelta(seconds=0)

    @classmethod
    def from_program_session(cls, session, end_time, duration_for_tests=None):
        """
        Create a CompletedProgramSession from an existing ProgramSession.
        This factory method makes it easy to convert a running session to a completed one.
        """
        return cls(
            exe_path=session.exe_path,
            process_name=session.process_name,
            window_title=session.window_title,
            detail=session.detail,
            start_time=session.start_time,
            end_time=end_time,
            productive=session.productive,
            duration_for_tests=duration_for_tests
        )
    
    def __str__(self):
        return (f"CompletedProgramSession(exe_path='{self.exe_path}', process_name='{self.process_name}', \n\t"
                f"title='{self.window_title}', detail='{self.detail}', \n\t"
                f"start_time='{self.start_time}', \n\t"
                f"end_time='{self.end_time}', duration='{self.duration}', productive='{self.productive}')")

    # TODO: Transfer whole codebase to use 2-3 vers of the program session.


class ChromeSession:
    domain: str
    detail: str
    start_time: UserLocalTime
    productive: bool

    def __init__(self, domain, detail, start_time, productive=False):
        self.domain = domain
        self.detail = detail
        self.start_time = start_time
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
        return f"ChromeSession(domain='{self.domain}', detail='{self.detail}', \n\tstart_time='{self.start_time}', \n\tproductive='{self.productive}')"


class CompletedChromeSession(ChromeSession):
    end_time: UserLocalTime
    duration: timedelta

    def __init__(self, domain, detail, start_time, end_time, productive=False, duration_for_tests=None):
        # Initialize the base class first
        """Only use duration arg in testing. Don't use it otherwise. 'duration_for_tests' exists only for e2e tests thresholds"""
        super().__init__(
            domain=domain,
            detail=detail,
            start_time=start_time,
            productive=productive
        )
        
        # Add the fields specific to CompletedChromeSession
        self.end_time = end_time
        
        # Calculate duration
        if start_time and end_time:
            self.duration = end_time - start_time
        elif duration_for_tests:
            self.duration = duration_for_tests
        else:
            self.duration = timedelta(seconds=0)

    @classmethod
    def from_chrome_session(cls, session, end_time, duration_for_tests=None):
        """
        Create a CompletedChromeSession from an existing ChromeSession.
        This factory method makes it easy to convert a running session to a completed one.
        """
        return cls(
            domain=session.domain,
            detail=session.detail,
            start_time=session.start_time,
            end_time=end_time,
            productive=session.productive,
            duration_for_tests=duration_for_tests
        )

    def __str__(self):
        return f"CompletedChromeSession(domain='{self.domain}', detail='{self.detail}', \n\tstart_time='{self.start_time}', \n\tend_time='{self.end_time}', duration='{self.duration}', \n\tproductive='{self.productive}')"

# TODO: Convert to use CompletedChromeSession to avoid that gross "start_time is not None" bs

class TabChangeEventWithLtz:
    tab_title: str
    url: str
    start_time_with_tz: datetime

    def __init__(self, tab_title, url, start_time_with_tz):
        self.tab_title = tab_title
        self.url = url
        self.start_time_with_tz = start_time_with_tz

    def __str__(self) -> str:
        """Custom string representation of the TabChangeEvent."""
        formatted_time = self.start_time_with_tz.strftime("%Y-%m-%d %H:%M:%S")
        return f"TabChangeEvent(tabTitle='{self.tab_title}', url='{self.url}', startTime='{formatted_time}')"


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
        start_formatted = self.start_time.strftime("%m-%d %H:%M:%S")
        end_formatted = self.end_time.strftime("%m-%d %H:%M:%S")
        return f"Peripheral aggregate from {start_formatted} to {end_formatted} with {self.count} events"


class KeyboardAggregate(PeripheralAggregate):
    """
    Keyboard-specific implementation of PeripheralAggregate.
    """

    def __str__(self):
        start_formatted = self.start_time.strftime("%m-%d %H:%M:%S")
        end_formatted = self.end_time.strftime("%m-%d %H:%M:%S")
        return f"Keyboard aggregate from {start_formatted} to {end_formatted} with {self.count} events"


class MouseAggregate(PeripheralAggregate):
    """
    Mouse-specific implementation of PeripheralAggregate.
    """

    def __str__(self):
        start_formatted = self.start_time.strftime("%m-%d %H:%M:%S")
        end_formatted = self.end_time.strftime("%m-%d %H:%M:%S")
        return f"Mouse aggregate from {start_formatted} to {end_formatted} with {self.count} events"


class MouseMoveWindow:
    def __init__(self, start_of_window: UserLocalTime, end_of_window: UserLocalTime, source=None):
        """Where the mouse was is irrelevant. From when to when it was moving is the important part."""
        self.start_time: UserLocalTime = start_of_window
        self.end_time: UserLocalTime = end_of_window
        self.source = source

    def __str__(self):
        if self.source:
            return f"Mouse movement from {self.start_time} to {self.end_time} - {self.source}"
        return f"Mouse movement from {self.start_time} to {self.end_time} : nameless"
