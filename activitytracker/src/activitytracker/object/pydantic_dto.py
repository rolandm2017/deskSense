# pydantic_dto.py
from enum import Enum

from pydantic import BaseModel

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
            url=event.url,
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
            url=event.url,
            player_state=event.playerState,
            show_name=event.showName,
        )
