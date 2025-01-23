from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from src.db.models import TimelineEntryObj


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


# For the uh, dashboard


class DailyProgramSummarySchema(BaseModel):
    id: int
    programName: str
    hoursSpent: float
    gatheringDate: datetime

    model_config = ConfigDict(from_attributes=True)  # This enables ORM mode


class BarChartContent(BaseModel):
    columns: List[DailyProgramSummarySchema]  # Use the Pydantic schema instead

    model_config = ConfigDict(from_attributes=True)


class TimelineEntrySchema(BaseModel):
    id: str  # This will map to clientFacingId from the SQLAlchemy model
    group: str  # This will map from ChartEventType enum
    content: str
    start: datetime
    end: datetime

    model_config = ConfigDict(from_attributes=True)

    # Optional: Add a method to convert from SQLAlchemy model
    @classmethod
    def from_orm_model(cls, db_model: TimelineEntryObj) -> 'TimelineEntrySchema':
        return cls(
            id=db_model.clientFacingId,
            group=db_model.group.value,  # Convert enum to string
            content=db_model.content,
            start=db_model.start,
            end=db_model.end
        )


class TimelineRows(BaseModel):
    mouseRows: List[TimelineEntrySchema]
    keyboardRows: List[TimelineEntrySchema]

# Chrome stuff


class URLDelivery(BaseModel):
    tabTitle: str
    url: str
