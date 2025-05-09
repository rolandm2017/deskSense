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


class TabChangeEventWithUnknownTz(BaseModel):
    tabTitle: str
    url: str
    startTime: datetime

    def __str__(self) -> str:
        """Custom string representation of the TabChangeEvent."""
        formatted_time = self.startTime.strftime("%Y-%m-%d %H:%M:%S")
        return f"TabChangeEvent(tabTitle='{self.tabTitle}', url='{self.url}', startTime='{formatted_time}')"


class UtcDtTabChange(BaseModel):
    tabTitle: str
    url: str
    startTime: datetime

    def __str__(self) -> str:
        """Custom string representation of the TabChangeEvent."""
        formatted_time = self.startTime.strftime("%Y-%m-%d %H:%M:%S")
        return f"TabChangeEvent(tabTitle='{self.tabTitle}', url='{self.url}', startTime='{formatted_time}')"


class YouTubeEvent(UtcDtTabChange):
    channel: str
    player_state: PlayerState
    player_position_in_sec: int

    def __str__(self) -> str:
        """Custom string representation of the YouTubeEvent."""
        formatted_time = self.startTime.strftime("%Y-%m-%d %H:%M:%S")
        return f"YouTubeEvent(tabTitle='{self.tabTitle}', url='{self.url}', chan='{self.channel}', startTime='{formatted_time}')"


# Video recording stuff


class VideoCreateEvent(BaseModel):
    title: str
    created_at: datetime


class FrameCreateEvent(BaseModel):
    video_id: int
    created_at: datetime
    frame_number: int


class VideoCreateConfirmation(BaseModel):
    video_id: int
