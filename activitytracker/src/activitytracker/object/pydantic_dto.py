# pydantic_dto.py
from pydantic import BaseModel, field_validator

from datetime import datetime

from typing import List, Optional, Union

from activitytracker.object.enums import PlayerState
from activitytracker.util.time_wrappers import UserLocalTime


class TabChangeEventWithUnknownTz(BaseModel):
    """
    It's a UtcDtTabChange but the local timezone isn't known
    """

    tabTitle: str
    url: str
    startTime: datetime

    def __str__(self) -> str:
        """Custom string representation of the TabChangeEventWithUnknownTz."""
        formatted_time = self.startTime.strftime("%Y-%m-%d %H:%M:%S")
        return f"TabChangeEventWithUnknownTz(tabTitle='{self.tabTitle}', url='{self.url}', startTime='{formatted_time}')"


class UtcDtTabChange(BaseModel):
    tabTitle: str
    url: str
    startTime: datetime

    def __str__(self) -> str:
        """Custom string representation of the TabChangeEvent."""
        formatted_time = self.startTime.strftime("%Y-%m-%d %H:%M:%S")
        return f"TabChangeEvent(tabTitle='{self.tabTitle}', url='{self.url}', startTime='{formatted_time}')"


class UtcDtStateChange(BaseModel):
    """Lives here to make everything that inherits from it a UtcDtStateChange"""


class VideoContentEvent(BaseModel):
    """Lives here to make everything that inherits from it a VideoContentEvent"""


class PlayerStateMixin:
    """Mixin to handle PlayerState validation"""

    @field_validator("playerState", mode="before")
    @classmethod
    def validate_player_state(cls, v):
        if isinstance(v, str):
            try:
                return PlayerState(v)
            except ValueError:
                raise ValueError(f"Invalid PlayerState: {v}")
        return v


class YouTubeTabChange(BaseModel, PlayerStateMixin):
    """Documents the user using a YouTube Watch page."""

    # NOTE that on May 19, this TabChange event meant ANY YouTube page.
    videoId: str
    tabTitle: str
    channel: str
    url: str
    startTime: datetime
    playerState: PlayerState


class YouTubePlayerChange(BaseModel, PlayerStateMixin):
    videoId: str
    tabTitle: str
    channel: str
    eventTime: datetime
    # url: str
    playerState: PlayerState  # Will be "paused" or "playing"


class NetflixTabChange(BaseModel, PlayerStateMixin):
    """Documents the user using a Netflix Watch page."""

    # At the time a user lands on the Netflix Watch page, the only info
    # the program will have is the videoId, until the user inputs media info by hand.
    tabTitle: str
    url: str
    startTime: datetime

    videoId: str
    playerState: PlayerState


class NetflixPlayerChange(BaseModel, PlayerStateMixin):
    tabTitle: str
    url: str
    eventTime: datetime
    videoId: str
    # url: str  # full url - is this really needed?
    showName: str
    playerState: PlayerState

    def __str__(self) -> str:
        return super().__str__()


class EventType(str, Enum):
    TAB_CHANGE = "tab_change"
    PLAYER_STATE = "player_state"


class Platform(str, Enum):
    YOUTUBE = "youtube"
    NETFLIX = "netflix"


# Base event with common fields
class BaseVideoEvent(BaseModel):
    platform: Platform
    event_type: EventType
    event_time: datetime  # Always UTC initially
    tab_title: str

    @field_validator("player_state", mode="before")
    @classmethod
    def validate_player_state(cls, v):
        if isinstance(v, str):
            try:
                return PlayerState(v)
            except ValueError:
                raise ValueError(f"Invalid PlayerState: {v}")
        return v


# Tab change events (user navigates to a watch page)
class TabChangeEvent(BaseVideoEvent):
    event_type: EventType = EventType.TAB_CHANGE
    url: str
    video_id: str
    player_state: PlayerState

    # Platform-specific optional fields
    channel: Optional[str] = None  # YouTube only
    show_name: Optional[str] = None  # Netflix only (if available)


# Player state events (play/pause)
class PlayerStateEvent(BaseVideoEvent):
    event_type: EventType = EventType.PLAYER_STATE
    url: str
    video_id: str
    player_state: PlayerState

    # Platform-specific optional fields
    channel: Optional[str] = None  # YouTube only
    show_name: Optional[str] = None  # Netflix only


# Union type for all events
VideoEvent = Union[TabChangeEvent, PlayerStateEvent]


# Factory function to create events from your current types
class VideoEventFactory:
    @staticmethod
    def from_youtube_tab_change(event: YouTubeTabChange) -> TabChangeEvent:
        return TabChangeEvent(
            platform=Platform.YOUTUBE,
            event_time=event.startTime,
            tab_title=event.tabTitle,
            url=event.url,
            video_id=event.videoId,
            player_state=event.playerState,
            channel=event.channel,
        )

    @staticmethod
    def from_youtube_player_change(event: YouTubePlayerChange) -> PlayerStateEvent:
        return PlayerStateEvent(
            platform=Platform.YOUTUBE,
            event_time=event.eventTime,
            tab_title=event.tabTitle,
            video_id=event.videoId,
            player_state=event.playerState,
            channel=event.channel,
        )

    @staticmethod
    def from_netflix_tab_change(event: NetflixTabChange) -> TabChangeEvent:
        return TabChangeEvent(
            platform=Platform.NETFLIX,
            event_time=event.startTime,
            tab_title=event.tabTitle,
            url=event.url,
            video_id=event.videoId,
            player_state=event.playerState,
        )

    @staticmethod
    def from_netflix_player_change(event: NetflixPlayerChange) -> PlayerStateEvent:
        return PlayerStateEvent(
            platform=Platform.NETFLIX,
            event_time=event.eventTime,
            tab_title=event.showName,  # Using showName as tab_title
            video_id=event.videoId,
            player_state=event.playerState,
            show_name=event.showName,
        )
