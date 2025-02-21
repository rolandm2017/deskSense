from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

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


class TabChangeEvent(BaseModel):
    tabTitle: str
    url: str
    startTime: datetime

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
