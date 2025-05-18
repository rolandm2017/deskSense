from pydantic import BaseModel

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


class VideoContentEvent(BaseModel):
    """Lives here to make everything that inherits from it a VideoContentEvent"""


class YouTubeTabChange(UtcDtTabChange):
    class YouTubePageEvent(VideoContentEvent):
        videoId: str
        tabTitle: str
        channel: str

        def __str__(self) -> str:
            formatted_time = self.startTime.strftime("%Y-%m-%d %H:%M:%S")
            return f"YouTubePageEvent(tabTitle='{self.tabTitle}', url='{self.url}', chan='{self.channel}', startTime='{formatted_time}')"

    pageEvent: YouTubePageEvent


class YouTubePlayerChange(UtcDtTabChange):
    class YouTubePlayerEvent(VideoContentEvent):
        videoId: str
        tabTitle: str
        channel: str
        playerState: str  # Will be "paused" or "playing"

        def __str__(self) -> str:
            formatted_time = self.startTime.strftime("%Y-%m-%d %H:%M:%S")
            return (
                f"YouTubePlayerEvent(videoId='{self.videoId}', tabTitle='{self.tabTitle}', url='{self.url}', chan='{self.channel}', startTime='{formatted_time}'"
                + f"\n\tplayerState: {self.playerState})"
            )

    playerEvent: YouTubePlayerEvent


class NetflixTabChange(UtcDtTabChange):
    class NetflixPageEvent(VideoContentEvent):
        videoId: str

    # At the time a user lands on the Netflix Watch page, the only info
    # the program will have is the videoId, until the user inputs media info by hand.
    pageEvent: NetflixPageEvent


class NetflixPlayerChange(UtcDtTabChange):
    class NetflixPlayerEvent(VideoContentEvent):
        # videoId aka urlId
        videoId: str
        url: str  # full url - is this really needed?
        showName: str

    playerEvent: NetflixPlayerEvent


class TabChangeEventWithUnknownTz(BaseModel):
    tabTitle: str
    url: str
    startTime: datetime

    def __str__(self) -> str:
        """Custom string representation of the TabChangeEvent."""
        formatted_time = self.startTime.strftime("%Y-%m-%d %H:%M:%S")
        return f"TabChangeEvent(tabTitle='{self.tabTitle}', url='{self.url}', startTime='{formatted_time}')"
