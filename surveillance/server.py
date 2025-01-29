# server.py
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
import asyncio
# import time
from typing import Optional, List


from src.db.database import init_db, async_session_maker

from src.db.models import DailyProgramSummary, DailyChromeSummary
# from src.services import MouseService, KeyboardService, ProgramService, DashboardService, ChromeService
# from src.services import get_mouse_service, get_chrome_service, get_program_service, get_keyboard_service, get_dashboard_service
from src.object.pydantic_dto import (
    KeyboardReport,
    MouseReport,
    ProgramActivityReport,
    DailyProgramSummarySchema,
    DailyChromeSummarySchema,
    ProgramBarChartContent,
    ChromeBarChartContent, TimelineEntrySchema, TimelineRows, TabChangeEvent,
    VideoCreateEvent, FrameCreateEvent, VideoCreateConfirmation

)
from src.util.pydantic_factory import make_keyboard_log, make_mouse_log, make_program_log
from src.surveillance_manager import SurveillanceManager
from src.console_logger import ConsoleLogger

from src.services import (
    KeyboardService, MouseService, ProgramService, DashboardService, ChromeService, VideoService
)
from src.service_dependencies import (
    get_keyboard_service, get_mouse_service, get_program_service,
    get_dashboard_service, get_chrome_service,
    get_video_service
)

# Rest of your server.py code...

logger = ConsoleLogger()


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
    surveillance_state.manager = SurveillanceManager(async_session_maker)
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

# this is a dependency function, it's like a lifespan but scoped to a request


class HealthResponse(BaseModel):
    status: str
    detail: str | None = None


@app.get("/health", response_model=HealthResponse)
async def health_check(keyboard_service: KeyboardService = Depends(get_keyboard_service)):
    logger.log_purple("[LOG] health check")
    try:
        # FIXME: this should be on the app, not a local variable
        if not surveillance_state.manager.keyboard_tracker:
            return {"status": "error", "detail": "Tracker not initialized"}
        await keyboard_service.get_all_events()
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/report/keyboard/all", response_model=KeyboardReport)
async def get_all_keyboard_reports(keyboard_service: KeyboardService = Depends(get_keyboard_service)):
    logger.log_purple("[LOG] keyboard report - all")
    # FIXME: this should be on the app, not a local variable
    if not surveillance_state.manager.keyboard_tracker:
        raise HTTPException(status_code=500, detail="Tracker not initialized")

    events = await keyboard_service.get_all_events()
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
    # FIXME: this should be on the app, not a local variable
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


def program_summary_row_to_pydantic(v: DailyProgramSummary):
    return DailyProgramSummarySchema(id=v.id, programName=v.program_name, hoursSpent=v.hours_spent, gatheringDate=v.gathering_date)


def chrome_summary_row_to_pydantic(v: DailyChromeSummary):
    return DailyChromeSummarySchema(id=v.id, domainName=v.domain_name, hoursSpent=v.hours_spent, gatheringDate=v.gathering_date)


def manufacture_programs_bar_chart(program_data):
    return [program_summary_row_to_pydantic(r) for r in program_data]


def manufacture_chrome_bar_chart(program_data):
    return [chrome_summary_row_to_pydantic(r) for r in program_data]


@app.get("/dashboard/program/summaries", response_model=ProgramBarChartContent)
async def get_program_time_for_dashboard(dashboard_service: DashboardService = Depends(get_dashboard_service)):
    program_data = await dashboard_service.get_program_summary()
    if not isinstance(program_data, list):
        raise HTTPException(
            status_code=500, detail="Failed to retrieve program chart info")
    return ProgramBarChartContent(columns=manufacture_programs_bar_chart(program_data))

# FIXME: Alt Tab Window has 2.2 hours, while Google Chrome has 0.9
# Which obviously can't be true


@app.get("/dashboard/chrome/summaries", response_model=ChromeBarChartContent)
async def get_chrome_time_for_dashboard(dashboard_service: DashboardService = Depends(get_dashboard_service)):
    chrome_data = await dashboard_service.get_chrome_summary()
    if not isinstance(chrome_data, list):
        raise HTTPException(
            status_code=500, detail="Failed to retrieve Chrome chart info")
    return ChromeBarChartContent(columns=manufacture_chrome_bar_chart(chrome_data))


@app.get("/report/chrome")
async def get_chrome_report(chrome_service: ChromeService = Depends(get_chrome_service)):
    logger.log_purple("[LOG] Get chrome tabs")
    reports = await chrome_service.read_last_24_hrs()
    return reports


def write_temp_log(event: TabChangeEvent):
    with open("events.csv", "a") as f:
        out = f"{event.tabTitle.replace(",", "::")},{event.url},{
            str(event.startTime)}"
        f.write(out)
        f.write("\n")


@app.post("/chrome/tab", status_code=status.HTTP_204_NO_CONTENT)
async def receive_chrome_tab(
    tab_change_event: TabChangeEvent,
    chrome_service: ChromeService = Depends(get_chrome_service)
):
    logger.log_purple("[LOG] Chrome Tab Received")
    try:
        await chrome_service.add_to_arrival_queue(tab_change_event)
        return  # Returns 204 No Content
    except Exception as e:
        print(e, '260ru')
        raise HTTPException(
            status_code=500,
            detail="A problem occurred in Chrome Service"
        )

# TODO: Endpoint for the Camera stuff


@app.post("/video/new", response_model=VideoCreateConfirmation)
async def receive_video_info(video_create_event: VideoCreateEvent, video_service: VideoService = Depends(get_video_service)):
    logger.log_purple("[LOG] Video create event")
    try:
        video_id = await video_service.create_new_video(video_create_event)
        return VideoCreateConfirmation(video_id=video_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="A problem occurred in Video Service"
        )


@app.post("/video/frame", status_code=status.HTTP_204_NO_CONTENT)
async def receive_frame_info(frame_create_event: FrameCreateEvent, video_service: VideoService = Depends(get_video_service)):
    logger.log_purple("[LOG] Video create event")
    try:
        await video_service.add_frame_to_video(frame_create_event)
        return
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="A problem occurred in Video Service"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
