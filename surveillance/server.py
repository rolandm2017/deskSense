# server.py
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
# import time
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from pydantic import BaseModel

from src.db.database import get_db, init_db, AsyncSession, async_session_maker
from src.db.dao.mouse_dao import MouseDao
from src.db.dao.keyboard_dao import KeyboardDao
from src.db.dao.program_dao import ProgramDao
from src.db.dao.timeline_entry_dao import TimelineEntryDao
from src.db.dao.daily_summary_dao import DailySummaryDao
from src.db.models import MouseMove, Program, DailyProgramSummary, TimelineEntryObj
from src.services import MouseService, KeyboardService, ProgramService, DashboardService
from src.object.dto import TypingSessionDto, MouseMoveDto, ProgramDto
from src.surveillance_manager import SurveillanceManager
from src.console_logger import ConsoleLogger


logger = ConsoleLogger()

# Add these dependency functions at the top of your file


async def get_keyboard_service(db: AsyncSession = Depends(get_db)) -> KeyboardService:
    return KeyboardService(KeyboardDao(async_session_maker))


async def get_mouse_service(db: AsyncSession = Depends(get_db)) -> MouseService:
    return MouseService(MouseDao(async_session_maker))


async def get_program_service(db: AsyncSession = Depends(get_db)) -> ProgramService:
    return ProgramService(ProgramDao(async_session_maker))


async def get_dashboard_service(db: AsyncSession = Depends(get_db)) -> DashboardService:
    return DashboardService(TimelineEntryDao(async_session_maker), DailySummaryDao(async_session_maker))


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


# class TimelineEntry(BaseModel):
#     # ex: `mouse-${log.mouseEventId}`, ex2: `keyboard-${log.keyboardEventId}`,
#     id: str
#     group: str  # "mouse" or "keyboard"
#     # ex: `Mouse Event ${log.mouseEventId}`, ex2: `Typing Session ${log.keyboardEventId}`,
#     content: str
#     start: datetime
#     end: datetime  # TOD: make it *come out of the db* ready to go


# class TimelineRows(BaseModel):
#     mouseRows: List[TimelineEntry]
#     keyboardRows: List[TimelineEntry]


# class BarChartProgramEntry(BaseModel):
#     programName: str
#     hoursSpent: float

#
# For the uh, dashboard


class DailyProgramSummarySchema(BaseModel):
    id: int
    program_name: str
    hours_spent: float
    gathering_date: datetime

    class Config:
        from_attributes = True  # This enables ORM mode


class BarChartContent(BaseModel):
    columns: List[DailyProgramSummarySchema]  # Use the Pydantic schema instead

    class Config:
        from_attributes = True


class TimelineEntrySchema(BaseModel):
    id: str  # This will map to clientFacingId from the SQLAlchemy model
    group: str  # This will map from ChartEventType enum
    content: str
    start: datetime
    end: datetime

    class Config:
        from_attributes = True

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

# Main class in this file


class SurveillanceState:
    def __init__(self):
        self.manager: Optional[SurveillanceManager] = None
        self.tracking_task: Optional[asyncio.Task] = None
        self.is_running: bool = False
        self.db_session = None


surveillance_state = SurveillanceState()


def track_productivity():
    while surveillance_state.is_running:
        # surveillance_state.manager.program_tracker.track_window()
        surveillance_state.manager.program_tracker.attach_listener()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize application-wide resources
    await init_db()

    # Use the session_maker directly
    surveillance_state.manager = SurveillanceManager(
        # Pass session_maker instead of get_db()
        async_session_maker, shutdown_signal="TODO")
    surveillance_state.manager.start_trackers()

    yield

    # Shutdown
    surveillance_state.is_running = False

    print("Shutting down productivity tracking...")
    # surveillance_state.tracking_task.cancel()
    if surveillance_state.manager:
        surveillance_state.manager.cleanup()
        # time.sleep(2)


app = FastAPI(lifespan=lifespan, root_path="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def make_keyboard_log(r: TypingSessionDto):
    if not hasattr(r, "start_time") or not hasattr(r, "end_time"):
        raise AttributeError("A timestamp field was missing")
    try:
        return KeyboardLog(
            keyboardEventId=r.id if hasattr(r, 'id') else None,
            startTime=r.start_time,
            endTime=r.end_time,
        )
    except AttributeError as e:
        raise e


def make_mouse_log(r: MouseMoveDto):
    try:
        return MouseLog(
            mouseEventId=r.id if hasattr(r, 'id') else None,
            startTime=r.start_time,
            endTime=r.end_time
        )
    except AttributeError as e:
        raise e


def make_program_log(r: ProgramDto):
    try:
        return ProgramActivityLog(
            programEventId=r.id if hasattr(r, 'id') else None,
            window=r.window,
            detail=r.detail,
            startTime=r.start_time,
            endTime=r.end_time,
            productive=r.productive
        )
    except AttributeError as e:
        raise e


@app.get("/report/keyboard/all", response_model=KeyboardReport)
async def get_all_keyboard_reports(keyboard_service: KeyboardService = Depends(get_keyboard_service)):
    logger.log_purple("[LOG] keyboard report - all")
    if not surveillance_state.manager.keyboard_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")

    events = await keyboard_service.get_all_events()
    print(len(events), '127ru')
    if not isinstance(events, list):
        raise HTTPException(
            status_code=500, detail="Failed to generate keyboard report")

    logs = [make_keyboard_log(e) for e in events]
    print(type(logs), type(logs[1]))
    return KeyboardReport(count=len(events), keyboardLogs=logs)


@app.get("/report/keyboard", response_model=KeyboardReport)
async def get_keyboard_report(keyboard_service: KeyboardService = Depends(get_keyboard_service)):
    # async def get_keyboard_report(db: Session = Depends(get_db)):
    logger.log_purple("[LOG] keyboard report")
    if not surveillance_state.manager.keyboard_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")

    events = await keyboard_service.get_past_days_events()

    if not isinstance(events, list):
        raise HTTPException(
            status_code=500, detail="Failed to generate keyboard report")

    logs = [make_keyboard_log(e) for e in events]
    return KeyboardReport(count=len(events), keyboardLogs=logs)


@app.get("/report/mouse/all", response_model=MouseReport)
async def get_all_mouse_reports(mouse_service: MouseService = Depends(get_mouse_service)):
    logger.log_purple("[LOG] mouse report - all")
    if not surveillance_state.manager.mouse_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")

    events = await mouse_service.get_all_events()
    if not isinstance(events, list):
        raise HTTPException(
            status_code=500, detail="Failed to generate mouse report")

    reports = [make_mouse_log(e) for e in events]
    return MouseReport(count=len(reports), mouseLogs=reports)


@app.get("/report/mouse", response_model=MouseReport)
async def get_mouse_report(mouse_service: MouseService = Depends(get_mouse_service)):
    logger.log_purple("[LOG] mouse report")
    if not surveillance_state.manager.mouse_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")

    events = await mouse_service.get_past_days_events()
    if not isinstance(events, list):
        raise HTTPException(
            status_code=500, detail="Failed to generate mouse report")

    reports = [make_mouse_log(e) for e in events]
    return MouseReport(count=len(reports), mouseLogs=reports)


@app.get("/report/program/all", response_model=ProgramActivityReport)
async def get_all_program_reports(program_service: ProgramService = Depends(get_program_service)):
    if not surveillance_state.manager.program_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")

    events = await program_service.get_all_events()
    if not isinstance(events, list):
        raise HTTPException(
            status_code=500, detail="Failed to generate program report")

    reports = [make_program_log(e) for e in events]
    return ProgramActivityReport(count=len(reports), programLogs=reports)


@app.get("/report/program", response_model=ProgramActivityReport)
async def get_program_activity_report(program_service: ProgramService = Depends(get_program_service)):
    if not surveillance_state.manager.program_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")

    events = await program_service.get_past_days_events()
    if not isinstance(events, list):
        raise HTTPException(
            status_code=500, detail="Failed to generate program report")

    reports = [make_program_log(e) for e in events]
    return ProgramActivityReport(count=len(reports), programLogs=reports)


@app.get("/dashboard/timeline", response_model=TimelineRows)
async def get_timeline_for_dashboard(dashboard_service: DashboardService = Depends(get_dashboard_service)):
    mouse_rows, keyboard_rows = await dashboard_service.get_timeline()
    if not isinstance(mouse_rows, list) or not isinstance(keyboard_rows, list):
        raise HTTPException(
            status_code=500, detail="Failed to retrieve timeline info")

    # Convert SQLAlchemy models to Pydantic models
    pydantic_mouse_rows = [
        TimelineEntrySchema.from_orm_model(row) for row in mouse_rows]
    pydantic_keyboard_rows = [
        TimelineEntrySchema.from_orm_model(row) for row in keyboard_rows]

    return TimelineRows(mouseRows=pydantic_mouse_rows, keyboardRows=pydantic_keyboard_rows)


@app.get("/dashboard/programs", response_model=BarChartContent)
async def get_program_time_for_dashboard(dashboard_service: DashboardService = Depends(get_dashboard_service)):
    program_data = await dashboard_service.get_program_summary()
    if not isinstance(program_data, list):
        raise HTTPException(
            status_code=500, detail="Failed to retrieve bar chart info")
    print(program_data, '304ru')
    return BarChartContent(columns=program_data)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
