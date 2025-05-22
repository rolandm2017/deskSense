# classes.py
# For various classes
from abc import ABC, abstractmethod

from datetime import datetime, timedelta, timezone

from typing import Optional, TypedDict

from activitytracker.config.definitions import window_push_length
from activitytracker.object.video_classes import (
    NetflixInfo,
    VideoInfo,
    VlcInfo,
    YouTubeInfo,
)
from activitytracker.tz_handling.time_formatting import parse_time_string
from activitytracker.util.errors import SessionClosedError
from activitytracker.util.time_wrappers import UserLocalTime


class SessionLedger:
    """
    A testing helper.

    Records the changes in time that reach the ActivityRecorder layer.
    """

    def __init__(self, name):
        self.total = 0
        self.name = name
        self.open = True
        self.DEBUG = False

    def add_ten_sec(self):
        """Proof that the add_ten_sec Recorder method occurred."""
        if self.open:
            if self.DEBUG:
                print(f"Ledger for {self.name}: Adding ten sec for total {self.total}")
            self.total += window_push_length
        else:
            raise SessionClosedError("Tried to push window after deduction")

    def extend_by_n(self, amount):
        """Proof that the deduct_duration method was called with a value."""
        self.open = False  # Cannot window push after deduct_duration
        if self.DEBUG:
            print(f"Ledger for {self.name}: Extend by n for total {self.total}")
        self.total += amount

    def get_total(self):
        return self.total


class ActivitySession(ABC):
    """Base class for all activity sessions that should never be instantiated directly."""

    start_time: UserLocalTime
    productive: bool
    ledger: SessionLedger
    video_info: Optional[VideoInfo] = None

    def __init__(self, start_time, productive, name):
        self.start_time = start_time
        self.productive = productive
        self.ledger = SessionLedger(name)

    @abstractmethod
    def to_completed(self, end_time):
        """Convert to a completed session."""
        pass


class ProgramSession(ActivitySession):
    exe_path: str
    process_name: str
    window_title: str
    detail: str
    # start_time: UserLocalTime  # exists in ActivitySession
    end_time: Optional[UserLocalTime]
    duration: Optional[timedelta]
    video_info: Optional[VlcInfo] = None

    # productive: bool  # exists in ActivitySession

    def __init__(
        self,
        exe_path="",
        process_name="",
        window_title="",
        detail="",
        start_time=UserLocalTime(datetime(2000, 1, 1, tzinfo=timezone.utc)),
        video_info=None,
        productive=False,
    ):
        # IF you remove the default args for this class, then you will have to do A LOT of cleanup in the test data.
        super().__init__(start_time, productive, process_name)
        self.exe_path = exe_path
        self.process_name = process_name
        self.window_title = window_title
        self.detail = detail
        self.video_info = video_info
        self.end_time = None
        self.duration = None

    def to_completed(self, end_time: UserLocalTime):
        """Similar to to_completed in the other type"""
        completed = CompletedProgramSession(
            exe_path=self.exe_path,
            process_name=self.process_name,
            window_title=self.window_title,
            detail=self.detail,
            #
            start_time=self.start_time,
            end_time=end_time,
            productive=self.productive,
        )
        completed.ledger = self.ledger
        return completed

    def get_name(self):
        """Useful because a string id property isn't common across both classes"""
        return self.process_name

    def parse_time_string(self, time_str):
        return parse_time_string(time_str)

    def __str__(self):
        return f"ProgramSession(exe_path='{self.exe_path}', process_name='{self.process_name}', \n\ttitle='{self.window_title}', detail='{self.detail}', \n\tstart_time='{self.start_time}', \n\tproductive='{self.productive}',\n\tledger='{self.ledger.get_total()}')"


class CompletedProgramSession(ProgramSession):
    end_time: UserLocalTime
    duration: timedelta

    def __init__(
        self,
        exe_path="",
        process_name="",
        window_title="",
        detail="",
        video_info=None,
        start_time=UserLocalTime(datetime(2000, 1, 1, tzinfo=timezone.utc)),
        end_time=UserLocalTime(datetime(2000, 1, 1, tzinfo=timezone.utc)),
        productive=False,
        duration_for_tests=None,
    ):
        """Only use duration arg in testing. Don't use it otherwise. 'duration_for_tests' exists only for e2e tests thresholds"""
        # TODO: Reorder it so productive is further up in the constructor.
        # Problem statement: I have to write the end time before the productive bool.
        # That's out of order. Sometimes there's no end time; there's always productive.

        # Initialize the base class first
        super().__init__(
            exe_path=exe_path,
            process_name=process_name,
            window_title=window_title,
            detail=detail,
            video_info=video_info,
            start_time=start_time,
            productive=productive,
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

    def __str__(self):
        return (
            f"CompletedProgramSession(exe_path='{self.exe_path}', process_name='{self.process_name}', \n\t"
            f"title='{self.window_title}', detail='{self.detail}', \n\t"
            f"start_time='{self.start_time}', \n\t"
            f"end_time='{self.end_time}', duration='{self.duration}', productive='{self.productive}', \n\tledger='{self.ledger.get_total()}')"
        )

    # TODO: Transfer whole codebase to use 2-3 vers of the program session.


class ChromeSession(ActivitySession):
    domain: str
    detail: str
    # start_time: UserLocalTime  # exists in ActivitySession
    end_time: Optional[UserLocalTime]
    duration: Optional[timedelta]
    video_info: Optional[YouTubeInfo | NetflixInfo] = None
    # productive: bool  # exists in ActivitySession

    def __init__(self, domain, detail, start_time, productive=False, video_info=None):
        super().__init__(start_time, productive, domain)
        self.domain = domain
        self.detail = detail
        self.video_info = video_info
        self.end_time = None
        self.duration = None

    def to_completed(self, end_time: UserLocalTime):
        """Similar to to_completed in the other type"""
        completed = CompletedChromeSession(
            domain=self.domain,
            detail=self.detail,
            video_info=self.video_info,
            #
            start_time=self.start_time,
            end_time=end_time,
            productive=self.productive,
        )
        completed.ledger = self.ledger
        return completed

    def get_name(self):
        """Useful because a string id property isn't common across both classes"""
        return self.domain

    @staticmethod
    def parse_time_string(time_str):
        return parse_time_string(time_str)

    def __str__(self):
        return f"ChromeSession(domain='{self.domain}', detail='{self.detail}', \n\tstart_time='{self.start_time}', \n\tproductive='{self.productive}', \n\tledger='{self.ledger.get_total()}')"


# class ChromeSessionWithVideo(ChromeSession):
#     video_details: YouTubeContent | NetflixContent

#     def __init__(self, domain, detail, start_time, video_details, productive=False):
#         super().__init__(domain, detail, start_time, productive)


class CompletedChromeSession(ChromeSession):
    end_time: UserLocalTime
    duration: timedelta

    def __init__(
        self,
        domain,
        detail,
        video_info=None,
        start_time=UserLocalTime(datetime(2000, 1, 1, tzinfo=timezone.utc)),
        end_time=UserLocalTime(datetime(2000, 1, 1, tzinfo=timezone.utc)),
        productive=False,
        duration_for_tests=None,
    ):
        # Initialize the base class first
        """Only use duration arg in testing. Don't use it otherwise. 'duration_for_tests' exists only for e2e tests thresholds"""
        super().__init__(
            domain=domain,
            detail=detail,
            start_time=start_time,
            productive=productive,
            video_info=video_info,
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

    def __str__(self):
        return f"CompletedChromeSession(domain='{self.domain}', detail='{self.detail}', \n\tstart_time='{self.start_time}', \n\tend_time='{self.end_time}', duration='{self.duration}', \n\tproductive='{self.productive}', \n\tledger='{self.ledger.get_total()}')"


class VideoSession(ActivitySession):
    """
    Needed to enable packaging relevant info for the video DAOs.
    """

    media_title: str
    channel_info: str
    # start_time: UserLocalTime  # exists in ActivitySession
    video_info: YouTubeInfo | NetflixInfo | VlcInfo

    def __init__(self, media_title, channel_info, video_info, start_time, productive, name):
        super().__init__(start_time, productive, name)
        self.media_title = media_title
        self.channel_info = channel_info  # Or FolderName or Series?
        self.video_info = video_info

    @staticmethod
    def from_other_type(session: ProgramSession | ChromeSession):
        """
        Necessary to package like this so start_time, end_time, duration,
        and even media info (title, season) live nicely in one terse package.
        """
        if isinstance(session, ProgramSession):
            return VideoSession.from_program_session(session)
        else:
            return VideoSession.from_chrome_session(session)

    @staticmethod
    def from_program_session(session: ProgramSession):
        """Works with a VLC Info object"""
        return VideoSession(
            session.video_info.file,
            session.video_info.folder,
            session.video_info,
            session.start_time,
            session.productive,
            session.video_info.get_name(),
        )

    @staticmethod
    def from_chrome_session(session: ChromeSession):
        return VideoSession(
            session.video_info.get_name(),
            # FIXME: How does Netflix media title get in here?
            session.video_info.channel_name,
            session.video_info,
            session.start_time,
            session.productive,
            session.video_info.get_name(),
        )

    def to_completed(self, end_time: UserLocalTime):
        """Similar to to_completed in the other type"""
        completed = CompletedVideoSession(
            media_title=self.media_title,
            channel_info=self.channel_info,
            video_info=self.video_info,
            #
            start_time=self.start_time,
            end_time=end_time,
            productive=self.productive,
        )
        completed.ledger = self.ledger
        return completed


class CompletedVideoSession(VideoSession):
    end_time: UserLocalTime
    duration: timedelta

    def __init__(
        self, media_title, channel_info, video_info, start_time, end_time, productive, name
    ):
        super().__init__(media_title, channel_info, video_info, start_time, productive, name)
        self.end_time = end_time
        self.duration = end_time - start_time


class ProgramSessionDict(TypedDict):
    os: str
    pid: int | None
    process_name: str
    exe_path: str
    window_title: str


class TabChangeEventWithLtz:
    tab_title: str
    url: str
    start_time_with_tz: UserLocalTime
    youtube_info: Optional[YouTubeInfo]
    netflix_info: Optional[NetflixInfo]

    def __init__(self, tab_title, url, start_time_with_tz, video_info=None):
        self.tab_title = tab_title
        self.url = url
        self.start_time_with_tz = start_time_with_tz
        if isinstance(video_info, YouTubeInfo):
            self.youtube_info = video_info
            self.netflix_info = None
        elif isinstance(video_info, NetflixInfo):
            self.youtube_info = None
            self.netflix_info = video_info

    def __str__(self) -> str:
        """Custom string representation of the TabChangeEventWithLtz."""
        formatted_time = self.start_time_with_tz.strftime("%Y-%m-%d %H:%M:%S.%f")[
            :-3
        ]  # Truncate to milliseconds
        return f"TabChangeEventWithLtz(tabTitle='{self.tab_title}', startTime='{formatted_time}', \n\tyoutube_info='{self.youtube_info}', netflix_info='{self.netflix_info}')"


class PlayerStateChangeEventWithLtz:
    tab_title: str
    # url: str
    event_time_with_tz: UserLocalTime
    youtube_info: Optional[YouTubeInfo]
    netflix_info: Optional[NetflixInfo]

    def __init__(self, tab_title, event_time_with_tz, video_info=None):
        self.tab_title = tab_title
        # self.url = url
        self.event_time_with_tz = event_time_with_tz
        if isinstance(video_info, YouTubeInfo):
            self.youtube_info = video_info
            self.netflix_info = None
        elif isinstance(video_info, NetflixInfo):
            self.youtube_info = None
            self.netflix_info = video_info

    def __str__(self) -> str:
        """Custom string representation of the PlayerStateChangeEventWithLtz."""
        formatted_time = self.event_time_with_tz.strftime("%Y-%m-%d %H:%M:%S.%f")[
            :-3
        ]  # Truncate to milliseconds
        return f"PlayerStateChangeEventWithLtz(\n\ttabTitle='{self.tab_title}', startTime='{formatted_time}', \n\tyoutube_info='{self.youtube_info}', \n\tnetflix_info='{self.netflix_info}')"


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
    def __init__(
        self, start_of_window: UserLocalTime, end_of_window: UserLocalTime, source=None
    ):
        """Where the mouse was is irrelevant. From when to when it was moving is the important part."""
        self.start_time: UserLocalTime = start_of_window
        self.end_time: UserLocalTime = end_of_window
        self.source = source

    def __str__(self):
        if self.source:
            return (
                f"Mouse movement from {self.start_time} to {self.end_time} - {self.source}"
            )
        return f"Mouse movement from {self.start_time} to {self.end_time} : nameless"
