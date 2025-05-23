# pydantic_video_dto.py
from enum import Enum

from pydantic import BaseModel, field_validator

from datetime import datetime

from typing import List, Optional, Union

from activitytracker.object.enums import PlayerState
from activitytracker.util.time_wrappers import UserLocalTime


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
    url: str
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
