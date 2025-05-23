# pydantic_dto.py
from pydantic import BaseModel, field_validator

from datetime import datetime

from typing import List, Optional

from activitytracker.object.enums import PlayerState
from activitytracker.util.time_wrappers import UserLocalTime


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


class YouTubeTabChange(UtcDtTabChange, PlayerStateMixin):
    """Documents the user using a YouTube Watch page."""

    # NOTE that on May 19, this TabChange event meant ANY YouTube page.

    videoId: str
    channel: str
    playerState: PlayerState


class YouTubePlayerChange(BaseModel, PlayerStateMixin):
    tabTitle: str
    eventTime: datetime
    videoId: str
    # url: str
    tabTitle: str
    channel: str
    playerState: PlayerState  # Will be "paused" or "playing"


class NetflixTabChange(UtcDtTabChange, PlayerStateMixin):
    """Documents the user using a Netflix Watch page."""

    # At the time a user lands on the Netflix Watch page, the only info
    # the program will have is the videoId, until the user inputs media info by hand.
    videoId: str
    playerState: PlayerState


class NetflixPlayerChange(BaseModel, PlayerStateMixin):
    eventTime: datetime
    videoId: str
    # url: str  # full url - is this really needed?
    showName: str
    playerState: PlayerState

    def __str__(self) -> str:
        return super().__str__()


class TabChangeEventWithUnknownTz(BaseModel):
    tabTitle: str
    url: str
    startTime: datetime

    def __str__(self) -> str:
        """Custom string representation of the TabChangeEvent."""
        formatted_time = self.startTime.strftime("%Y-%m-%d %H:%M:%S")
        return f"TabChangeEvent(tabTitle='{self.tabTitle}', url='{self.url}', startTime='{formatted_time}')"
