from pydantic import BaseModel, ConfigDict
from typing import List
from datetime import datetime

from activitytracker.db.models import PrecomputedTimelineEntry


class ProductivityBreakdown(BaseModel):
    day: datetime
    productiveHours: float
    leisureHours: float


class ProductivityBreakdownByWeek(BaseModel):
    days: List[ProductivityBreakdown]

# For the uh, dashboard


class DailyProgramSummarySchema(BaseModel):
    id: int
    programName: str
    hoursSpent: float
    gatheringDate: datetime

    model_config = ConfigDict(from_attributes=True)  # This enables ORM mode


class ProgramBarChartContent(BaseModel):
    columns: List[DailyProgramSummarySchema]  # Use the Pydantic schema instead

    model_config = ConfigDict(from_attributes=True)


class DayOfProgramContent(BaseModel):
    date: datetime
    content: ProgramBarChartContent


class WeeklyProgramContent(BaseModel):
    days: List[DayOfProgramContent]


class DailyDomainSummarySchema(BaseModel):
    id: int
    domainName: str
    hoursSpent: float
    gatheringDate: datetime

    model_config = ConfigDict(from_attributes=True)  # This enables ORM mode


class ChromeBarChartContent(BaseModel):
    columns: List[DailyDomainSummarySchema]  # Use the Pydantic schema instead

    model_config = ConfigDict(from_attributes=True)


class DayOfChromeContent(BaseModel):
    date: datetime
    content: ChromeBarChartContent


class WeeklyChromeContent(BaseModel):
    days: List[DayOfChromeContent]


class SinglePastWeekOfChromeContent(BaseModel):
    days: List[DayOfChromeContent]


class TimelineEntrySchema(BaseModel):
    id: str  # This will map to clientFacingId from the SQLAlchemy model
    group: str  # This will map from ChartEventType enum
    content: str
    start: datetime
    end: datetime

    model_config = ConfigDict(from_attributes=True)

    # Optional: Add a method to convert from SQLAlchemy model
    @classmethod
    def from_orm_model(cls, db_model: PrecomputedTimelineEntry) -> 'TimelineEntrySchema':
        try:
            # Note: If not for appeasing the IDE typing checker, this would be obj.property all the way down
            return cls(
                # Convert to string explicitly
                id=str(db_model.clientFacingId),
                group=db_model.group.value if hasattr(
                    db_model.group, 'value') else str(db_model.group),
                content=str(db_model.content),
                start=db_model.start if isinstance(
                    db_model.start, datetime) else datetime.fromisoformat(str(db_model.start)),
                end=db_model.end if isinstance(
                    db_model.end, datetime) else datetime.fromisoformat(str(db_model.end))
            )
        except:
            print(db_model)
            print("failed")
            raise ValueError("Failed with value")


class TimelineRows(BaseModel):
    mouseRows: List[TimelineEntrySchema]
    keyboardRows: List[TimelineEntrySchema]


class DayOfTimelineRows(BaseModel):
    date: datetime
    row: TimelineRows


class WeeklyTimeline(BaseModel):
    days: List[DayOfTimelineRows]  # expect 1 to 7
    start_date: datetime


class PartiallyPrecomputedWeeklyTimeline(BaseModel):
    beforeToday: List[DayOfTimelineRows]  # expect 0 to 6
    today: DayOfTimelineRows
    startDate: datetime


class TimelineEvent(BaseModel):
    logId: int
    startTime: datetime
    endTime: datetime


class ProgramTimelineContent(BaseModel):
    programName: str
    events: List[TimelineEvent]


class ProgramUsageTimeline(BaseModel):
    date: datetime
    programs:  List[ProgramTimelineContent]


class WeeklyProgramUsageTimeline(BaseModel):
    days: List[ProgramUsageTimeline]


class MouseEventsPayload(BaseModel):
    start_time: datetime
    end_time: datetime
    count: int
