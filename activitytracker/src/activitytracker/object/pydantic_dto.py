from pydantic import BaseModel

from datetime import datetime

from typing import List, Optional

from activitytracker.object.enums import PlayerState
from activitytracker.util.time_wrappers import UserLocalTime

# Reports


class KeyboardLog(BaseModel):
    keyboardEventId: Optional[int] = None
    startTime: datetime
    endTime: datetime


class KeyboardReport(BaseModel):
    count: int
    keyboardLogs: List[KeyboardLog]


class MouseLog(BaseModel):
    mouseEventId: Optional[int] = None
    startTime: datetime
    endTime: datetime


class MouseReport(BaseModel):
    count: int
    mouseLogs: List[MouseLog]


class ProgramActivityLog(BaseModel):
    programEventId: Optional[int] = None
    window: str
    detail: str
    startTime: datetime
    endTime: datetime
    productive: bool


class ProgramActivityReport(BaseModel):
    count: int
    programLogs: List[ProgramActivityLog]


# Chrome stuff


class VideoContentEvent(BaseModel):
    videoId: str
    # url: str  # These objects don't care about URL. That's just the ID.
    # These objs do not track startTime.
    # They only care about play, pause.

    def __str__(self) -> str:
        """Custom string representation of the TabChangeEvent."""
        formatted_time = self.startTime.strftime("%Y-%m-%d %H:%M:%S")
        return f"TabChangeEvent(tabTitle='{self.tabTitle}', url='{self.url}', startTime='{formatted_time}')"


class YouTubePageEvent(VideoContentEvent):
    tabTitle: str
    channel: str

    def __str__(self) -> str:
        formatted_time = self.startTime.strftime("%Y-%m-%d %H:%M:%S")
        return f"YouTubePageEvent(tabTitle='{self.tabTitle}', url='{self.url}', chan='{self.channel}', startTime='{formatted_time}')"


class YouTubePlayerEvent(VideoContentEvent):
    tabTitle: str
    channel: str
    playerState: str  # Will be "paused" or "playing"

    def __str__(self) -> str:
        formatted_time = self.startTime.strftime("%Y-%m-%d %H:%M:%S")
        return (
            f"YouTubePlayerEvent(videoId='{self.videoId}', tabTitle='{self.tabTitle}', url='{self.url}', chan='{self.channel}', startTime='{formatted_time}'"
            + f"\n\tplayerState: {self.playerState})"
        )


class NetflixPageEvent(VideoContentEvent):
    # Nothing different but the name


class NetflixPlayerEvent(VideoContentEvent):
    # videoId aka urlId on VideoContentEvent
    url: str  # full url - is this really needed?
    showName: str



class UtcDtTabChange(BaseModel):
    tabTitle: str
    url: str
    startTime: datetime

    def __str__(self) -> str:
        """Custom string representation of the TabChangeEvent."""
        formatted_time = self.startTime.strftime("%Y-%m-%d %H:%M:%S")
        return f"TabChangeEvent(tabTitle='{self.tabTitle}', url='{self.url}', startTime='{formatted_time}')"


class YouTubeTabChange(UtcDtTabChange):
    pageEvent: YouTubePageEvent


class YouTubePlayerChange(UtcDtTabChange):
    playerEvent: YouTubePlayerEvent


class NetflixTabChange(UtcDtTabChange):
    # At the time a user lands on the Netflix Watch page, the only info
    # the program will have is the videoId, until the user inputs media info by hand.
    pageEvent: NetflixPageEvent


class NetflixPlayerChange(UtcDtTabChange):
    playerEvent: NetflixPlayerEvent

class TabChangeEventWithUnknownTz(BaseModel):
    tabTitle: str
    url: str
    startTime: datetime

    def __str__(self) -> str:
        """Custom string representation of the TabChangeEvent."""
        formatted_time = self.startTime.strftime("%Y-%m-%d %H:%M:%S")
        return f"TabChangeEvent(tabTitle='{self.tabTitle}', url='{self.url}', startTime='{formatted_time}')"

