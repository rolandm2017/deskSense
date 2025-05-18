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
