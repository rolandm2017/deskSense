# server.py
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, status, Request
from fastapi import Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from contextlib import asynccontextmanager
from pydantic import BaseModel
import asyncio
# import time
from typing import Optional, List, Dict, Tuple
from datetime import date, datetime
from time import time


from src.db.database import init_db, async_session_maker
from src.db.models import DailyDomainSummary, DailyProgramSummary, ProgramSummaryLog

# from src.services import MouseService, KeyboardService, ProgramService, DashboardService, ChromeService
# from src.services import get_mouse_service, get_chrome_service, get_program_service, get_keyboard_service, get_dashboard_service
from src.object.pydantic_dto import (
    KeyboardReport,
    MouseReport,
    ProgramActivityReport,
    TabChangeEvent,
    VideoCreateEvent, FrameCreateEvent, VideoCreateConfirmation,

)

from src.object.dashboard_dto import (
    PartiallyPrecomputedWeeklyTimeline,
    ProductivityBreakdownByWeek,
    ProgramBarChartContent,
    ChromeBarChartContent,
    ProgramTimelineContent,
    ProgramUsageTimeline, TimelineEntrySchema,
    TimelineEvent, TimelineRows,
    WeeklyProgramContent, WeeklyChromeContent,
    WeeklyProgramUsageTimeline, WeeklyTimeline, DayOfTimelineRows
)

from src.util.pydantic_factory import (
    make_keyboard_log, make_mouse_log, make_program_log,
    manufacture_chrome_bar_chart, manufacture_programs_bar_chart,
    DtoMapper
)
from src.surveillance_manager import SurveillanceManager

from src.services.dashboard_service import DashboardService
from src.services.chrome_service import ChromeService

from src.services.services import (
    KeyboardService, MouseService, ProgramService, TimezoneService, VideoService
)
from src.service_dependencies import (
    get_keyboard_service, get_mouse_service, get_program_service,
    get_dashboard_service, get_chrome_service, get_activity_arbiter, get_timezone_service,
    get_video_service
)
from src.object.return_types import DaySummary

from src.util.console_logger import ConsoleLogger
from src.util.debug_logger import write_temp_log

# Import the router for report endpoints
from src.routes.report_routes import router as report_router

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


# def track_productivity():
#     while surveillance_state.is_running:
#         # surveillance_state.manager.program_tracker.track_window()
#         assert surveillance_state.manager is not None
#         # surveillance_state.manager.program_tracker.attach_listener()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize application-wide resources
    await init_db()

    # If you need to note when the computer starts up,
    # consider that the server will likely auto-run on startup
    # when it gets past development and onto being a typical daily use

    chrome_service = await get_chrome_service()
    arbiter = await get_activity_arbiter()
    # Use the session_maker directly
    surveillance_state.manager = SurveillanceManager(
        async_session_maker, chrome_service, arbiter)
    surveillance_state.manager.start_trackers()

    yield

    # Shutdown
    surveillance_state.is_running = False

    print("Shutting down productivity tracking...")
    # surveillance_state.tracking_task.cancel()
    if surveillance_state.manager:
        await surveillance_state.manager.cleanup()
        # time.sleep(2)


app = FastAPI(lifespan=lifespan, root_path="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(report_router)


class HealthResponse(BaseModel):
    status: str
    detail: str | None = None


@app.get("/health", response_model=HealthResponse)
async def health_check(keyboard_service: KeyboardService = Depends(get_keyboard_service)):
    logger.log_purple("[LOG] health check")
    try:
        # FIXME: this should be on the app, not a local variable
        if not surveillance_state and not surveillance_state.manager.keyboard_tracker:
            return {"status": "error", "detail": "Tracker not initialized"}
        await keyboard_service.get_all_events()
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/dashboard/timeline", response_model=TimelineRows)
async def get_timeline_for_dashboard(dashboard_service: DashboardService = Depends(get_dashboard_service)):
    mouse_rows, keyboard_rows = await dashboard_service.get_timeline_for_today()
    # // TODO: make this be given by day
    if not isinstance(mouse_rows, list) or not isinstance(keyboard_rows, list):
        raise HTTPException(
            status_code=500, detail="Failed to retrieve timeline info")

    # Convert SQLAlchemy models to Pydantic models
    pydantic_mouse_rows = [
        TimelineEntrySchema.from_orm_model(row) for row in mouse_rows]
    pydantic_keyboard_rows = [
        TimelineEntrySchema.from_orm_model(row) for row in keyboard_rows]

    return TimelineRows(mouseRows=pydantic_mouse_rows, keyboardRows=pydantic_keyboard_rows)


@app.get("/dashboard/program/summaries", response_model=ProgramBarChartContent)
async def get_program_time_for_dashboard(dashboard_service: DashboardService = Depends(get_dashboard_service)):
    program_data = await dashboard_service.get_program_summary()
    if not isinstance(program_data, list):
        raise HTTPException(
            status_code=500, detail="Failed to retrieve program chart info")
    return ProgramBarChartContent(columns=manufacture_programs_bar_chart(program_data))


@app.get("/dashboard/chrome/summaries", response_model=ChromeBarChartContent)
async def get_chrome_time_for_dashboard(dashboard_service: DashboardService = Depends(get_dashboard_service)):
    chrome_data = await dashboard_service.get_chrome_summary()
    if not isinstance(chrome_data, list):
        raise HTTPException(
            status_code=500, detail="Failed to retrieve Chrome chart info")
    return ChromeBarChartContent(columns=manufacture_chrome_bar_chart(chrome_data))


#
# By Week # By Week
# By Week # By Week # By Week
# By Week # By Week
#

@app.get("/dashboard/breakdown/week/{week_of}", response_model=ProductivityBreakdownByWeek)
async def get_productivity_breakdown(week_of: date = Path(..., description="Week starting date"),
                                     dashboard_service: DashboardService = Depends(get_dashboard_service)):
    weeks_overview: List[dict] = await dashboard_service.get_weekly_productivity_overview(week_of)
    if not isinstance(weeks_overview, list):
        raise HTTPException(
            status_code=500, detail="Failed to retrieve week of Chrome chart info")
    for some_dict in weeks_overview:
        if not isinstance(some_dict, dict):
            raise HTTPException(
                status_code=500, detail="Expected a list of dicts")

    return ProductivityBreakdownByWeek(days=DtoMapper.map_overview(weeks_overview))


@app.get("/dashboard/program/summaries/week", response_model=WeeklyProgramContent)
async def get_program_week_history(dashboard_service: DashboardService = Depends(get_dashboard_service)):
    week_of_data: List[DailyProgramSummary] = await dashboard_service.get_program_summary_weekly()
    # TODO: Test on Tuesday, Wednesday to see that they each get their own day
    if not isinstance(week_of_data, list):
        raise HTTPException(
            status_code=500, detail="Failed to retrieve week of program chart info")
    return WeeklyProgramContent(days=DtoMapper.map_programs(week_of_data))


@app.get("/dashboard/chrome/summaries/week", response_model=WeeklyChromeContent)
async def get_chrome_week_history(dashboard_service: DashboardService = Depends(get_dashboard_service)):
    week_of_unsorted_domain_summaries: List[DailyDomainSummary] = await dashboard_service.get_chrome_summary_weekly()
    # TODO: Test on Tuesday, Wednesday to see that they each get their own day

    if not isinstance(week_of_unsorted_domain_summaries, list):
        raise HTTPException(
            status_code=500, detail="Failed to retrieve week of Chrome chart info")
    for day in week_of_unsorted_domain_summaries:
        if not isinstance(day, DailyDomainSummary):
            raise HTTPException(
                status_code=500, detail="Did not receive a list of DailyDomainSummary objects")
    return WeeklyChromeContent(days=DtoMapper.map_chrome(week_of_unsorted_domain_summaries))


@app.get("/dashboard/chrome/summaries/week/{week_of}", response_model=WeeklyChromeContent)
async def get_previous_week_chrome_history(week_of: date = Path(..., description="Week starting date"),
                                           dashboard_service: DashboardService = Depends(get_dashboard_service)):
    week_of_unsorted_domain_summaries: List[DailyDomainSummary] = await dashboard_service.get_previous_week_chrome_summary(week_of)

    if not isinstance(week_of_unsorted_domain_summaries, list):
        raise HTTPException(
            status_code=500, detail="Failed to retrieve week of Chrome chart info")

    # Is a list of lists
    for day in week_of_unsorted_domain_summaries:
        if not isinstance(day, DailyDomainSummary):
            raise HTTPException(
                status_code=500, detail="Did not receive a list of Daily Domain Summaries, received instead:" + str(type(day)))

    # days = [DtoMapper.map_chrome(day) for day in package]
    days = DtoMapper.map_chrome(week_of_unsorted_domain_summaries)

    return WeeklyChromeContent(days=days)


@app.get("/dashboard/timeline/week", response_model=PartiallyPrecomputedWeeklyTimeline)
async def get_timeline_weekly(dashboard_service: DashboardService = Depends(get_dashboard_service)):
    days_before_today, todays_payload, latest_sunday = await dashboard_service.get_current_week_timeline()
    rows: List[DayOfTimelineRows] = []

    assert isinstance(todays_payload, dict)
    todays_date = todays_payload["date"]

    mouse_rows = todays_payload["mouse_events"]
    keyboard_rows = todays_payload["keyboard_events"]
    # Convert SQLAlchemy models to Pydantic models
    pydantic_mouse_rows = [
        TimelineEntrySchema.from_orm_model(row) for row in mouse_rows]
    pydantic_keyboard_rows = [
        TimelineEntrySchema.from_orm_model(row) for row in keyboard_rows]

    todays_row = TimelineRows(mouseRows=pydantic_mouse_rows,
                              keyboardRows=pydantic_keyboard_rows)

    todays_payload = DayOfTimelineRows(date=todays_date, row=todays_row)

    for day in days_before_today:
        assert isinstance(day, dict)
        mouse_rows = day["mouse_events"]
        keyboard_rows = day["keyboard_events"]
        # Convert SQLAlchemy models to Pydantic models
        pydantic_mouse_rows = [
            TimelineEntrySchema.from_orm_model(row) for row in mouse_rows]
        pydantic_keyboard_rows = [
            TimelineEntrySchema.from_orm_model(row) for row in keyboard_rows]

        row = TimelineRows(mouseRows=pydantic_mouse_rows,
                           keyboardRows=pydantic_keyboard_rows)

        row = DayOfTimelineRows(date=day["date"], row=row)
        rows.append(row)

    return PartiallyPrecomputedWeeklyTimeline(beforeToday=rows, today=todays_payload, startDate=latest_sunday)


@app.get("/dashboard/timeline/week/{week_of}", response_model=WeeklyTimeline)
async def get_previous_week_of_timeline(week_of: date = Path(..., description="Week starting date"),
                                        dashboard_service: DashboardService = Depends(get_dashboard_service)):
    days, start_of_week = await dashboard_service.get_specific_week_timeline(week_of)

    rows: List[DayOfTimelineRows] = []
    for day in days:
        assert isinstance(day, dict)
        mouse_rows = day["mouse_events"]
        keyboard_rows = day["keyboard_events"]

        pydantic_mouse_rows = [
            TimelineEntrySchema.from_orm_model(row) for row in mouse_rows]
        pydantic_keyboard_rows = [
            TimelineEntrySchema.from_orm_model(row) for row in keyboard_rows]
        row = TimelineRows(mouseRows=pydantic_mouse_rows,
                           keyboardRows=pydantic_keyboard_rows)
        row = DayOfTimelineRows(date=day["date"], row=row)
        rows.append(row)

    # TODO: Convert from UTC to PST for the client

    response = WeeklyTimeline(days=rows, start_date=start_of_week)

    return response


@app.get("/dashboard/programs/usage/timeline", response_model=WeeklyProgramUsageTimeline)
async def get_program_usage_timeline_for_present_week(
        dashboard_service: DashboardService = Depends(get_dashboard_service)):
    all_days, start_of_week = await dashboard_service.get_current_week_program_usage_timeline()

    days = []
    for day in all_days:
        programs: dict[str, ProgramSummaryLog] = day["program_usage_timeline"]
        # assert isinstance(programs, dict)
        date = day["date"]

        programs_content = []
        for key, value_list in programs.items():
            print(key, ": \n")

            timeline_events = []
            for program_log in value_list:
                # Assuming ProgramSummaryLog has startTime and endTime attributes
                timeline_event = TimelineEvent(
                    startTime=program_log.start_time,
                    endTime=program_log.end_time
                )
                timeline_events.append(timeline_event)

            content = ProgramTimelineContent(
                programName=key, events=timeline_events)
            programs_content.append(content)
        day_timeline = ProgramUsageTimeline(
            date=date, programs=programs_content)
        days.append(day_timeline)

        # program_timeline_content = ProgramTimelineContent(programName=)
        # program_usage_timeline = ProgramUsageTimeline(date=date, programs=package=[''])
    return WeeklyProgramUsageTimeline(days=days)


@app.get("/dashboard/programs/usage/timeline/{week_of}", response_model=WeeklyProgramUsageTimeline)
async def get_program_usage_timeline_by_week(week_of: date = Path(..., description="Week starting date"),
                                             dashboard_service: DashboardService = Depends(get_dashboard_service)):
    all_days, start_of_week = await dashboard_service.get_program_usage_timeline_for_week(week_of)

    days = []
    for day in all_days:
        programs: dict[str, ProgramSummaryLog] = day["program_usage_timeline"]
        date = day["date"]

        for key, value in programs.items():
            print(key, value)

        # program_timeline_content = ProgramTimelineContent(programName=)
        # program_usage_timeline = ProgramUsageTimeline(date=date, programs=package=[''])
    return WeeklyProgramUsageTimeline(days=days)


@app.get("/report/chrome")
async def get_chrome_report(chrome_service: ChromeService = Depends(get_chrome_service)):
    logger.log_purple("[LOG] Get chrome tabs")
    reports = await chrome_service.read_last_24_hrs()
    return reports


@app.post("/chrome/tab", status_code=status.HTTP_204_NO_CONTENT)
async def receive_chrome_tab(
    tab_change_event: TabChangeEvent,
    chrome_service: ChromeService = Depends(get_chrome_service),
    timezone_service: TimezoneService = Depends(get_timezone_service)
):
    logger.log_purple("[LOG] Chrome Tab Received")
    try:
        user_id = 1  # temp
        tz_for_user = timezone_service.get_tz_for_user(
            user_id)
        updated_tab_change_event = timezone_service.convert_tab_change_timezone(
            tab_change_event, tz_for_user)
        await chrome_service.tab_queue.add_to_arrival_queue(updated_tab_change_event)
        return  # Returns 204 No Content
    except Exception as e:
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

# FIXME Jan 28: Alt Tab Window has 2.2 hours, while Google Chrome has 0.9
# FIXME: Which obviously can't be true


# TODO Jan 28: When the computer shuts down, go to Chrome Summary, "end session"
# TODO: When the computer shuts down, go to Program Summary, "end session"
# TODO: Does Prgram Tracker need to know when shutdown occurs? Does it already kniw? Investigate

# TODO Jan 28: When shut down detected, the Chrome Session, the final one, should be concluded

# TODO Jan 28: When Chrome is exited, the final tab session should be concluded.
# TODO: So if ProgramTracker detects closing Chrome,

# FIXME Jan 28: At the end of every day, a new set of counters, per program, should be initialized
# FIXME: In other words, the day goes from Jan 24 -> Jan 25, the db goes "new rows start here"

# FIXME: Am getting values like 20, 12, 23, 20, 17, 19 from 'Alt-tab window' in the Daily Progrma Summary
# Hypothesis: ...
# FIXME: (1) One solution would be to only ever put in like 3 sec on alt tab. But that's crude.
# FIXME: (2) Another option would be to spend a whole day or two observing the growth of Alt Tab time in DailyProgramSummaries
# FIXME: Option (3): write a log file every time time is added to Alt-Tab Window


# TODO: Need to write to power-on-off-times on startup
# TODO: but how? the program legit isn't running yet

    # TODO: Install debug overlay. It could be:
    # Chrome & Programs -> CPU -> Overlay, DAOs.
    # It could be that I use State to handle generating Summary changes.
    # If state change, record summary of window.
    # So CPU knows about Chrome & Program state, & every time something changes, it yields a conclusion.
    # Then, neither the Chrome Service, nor Program Tracker, nor the DAOs, need to do any math. They're simple

# TODO Feb 26:
