# server.py
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, status, Request
from fastapi import Path
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager
from pydantic import BaseModel
import asyncio
# import time
from typing import Optional, List
from datetime import date, datetime, timezone
from time import time


from surveillance.src.db.database import init_db, async_session_maker, regular_session_maker
from surveillance.src.db.models import DailyDomainSummary, DailyProgramSummary, ProgramSummaryLog


from surveillance.src.routes.report_routes import router as report_router
from surveillance.src.routes.video_routes import router as video_routes

from surveillance.src.object.pydantic_dto import UtcDtTabChange, YouTubeEvent
from surveillance.src.object.classes import TabChangeEventWithLtz

from surveillance.src.object.dashboard_dto import (
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

from surveillance.src.facade.facade_singletons import get_keyboard_facade_instance, get_mouse_facade_instance
from surveillance.src.surveillance_manager import FacadeInjector, SurveillanceManager

from surveillance.src.services.dashboard_service import DashboardService
from surveillance.src.services.chrome_service import ChromeService
from surveillance.src.facade.receive_messages import MessageReceiver



from surveillance.src.services.tiny_services import TimezoneService

from surveillance.src.service_dependencies import (
    get_keyboard_service, get_mouse_service,     get_dashboard_service, get_chrome_service, get_activity_arbiter, get_timezone_service,
    get_video_service
)

from surveillance.src.util.console_logger import ConsoleLogger

from surveillance.src.util.pydantic_factory import (
    manufacture_chrome_bar_chart, manufacture_programs_bar_chart,
    DtoMapper
)

from surveillance.src.util.clock import UserFacingClock
from surveillance.src.util.time_wrappers import UserLocalTime
# from surveillance.src.facade.program_facade import ProgramApiFacadeCore

import sys
import os

# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
print("SERVER STARTING WITH UNBUFFERED OUTPUT")

logger = ConsoleLogger()


# Main class in this file
class SurveillanceState:
    def __init__(self):
        self.manager: Optional[SurveillanceManager] = None
        self.tracking_task: Optional[asyncio.Task] = None
        self.is_running: bool = False
        self.db_session = None


surveillance_state = SurveillanceState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize application-wide resources
    await init_db()

    # If you need to note when the computer starts up,
    # consider that the server will likely auto-run on startup
    # when it gets past development and onto being a typical daily use

    chrome_service = await get_chrome_service()
    arbiter = await get_activity_arbiter()

    user_facing_clock = UserFacingClock()

    def choose_program_facade(os):
        if os.is_windows:
            from surveillance.src.facade.program_facade_windows import WindowsProgramFacadeCore
            return WindowsProgramFacadeCore()
        else:
            from surveillance.src.facade.program_facade_ubuntu import UbuntuProgramFacadeCore
            return UbuntuProgramFacadeCore()

    facades = FacadeInjector(get_keyboard_facade_instance,
                             get_mouse_facade_instance, choose_program_facade)
    
    message_receiver = MessageReceiver("tcp://127.0.0.1:5555")
    surveillance_state.manager = SurveillanceManager(user_facing_clock,
                                                     async_session_maker, regular_session_maker, chrome_service, arbiter, facades, message_receiver)
    surveillance_state.manager.start_trackers()

    try:
        yield
    finally:
        # Shutdown
        surveillance_state.is_running = False

        print("Shutting down productivity tracking...")
        if surveillance_state.manager:
            try:
                # Use a timeout to ensure cleanup doesn't hang
                await asyncio.wait_for(surveillance_state.manager.cleanup(), timeout=5.0)

                # Also ensure the shutdown handler runs
                surveillance_state.manager.shutdown_handler()
                # await asyncio.wait_for(surveillance_state.manager.shutdown_handler(), timeout=5.0)
            except asyncio.TimeoutError:
                print("Cleanup timed out, forcing shutdown")
            except Exception as e:
                print(f"Error during cleanup: {e}")
                import traceback
                traceback.print_exc()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(report_router)
app.include_router(video_routes)


class HealthResponse(BaseModel):
    status: str
    detail: str | None = None


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    logger.log_purple("[LOG] health check")
    try:
        if not surveillance_state and not surveillance_state.manager.keyboard_tracker:
            return {"status": "error", "detail": "Tracker not initialized"}
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Health check failed: {str(e)}")


@app.get("/api/dashboard/timeline", response_model=TimelineRows)
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


@app.get("/api/dashboard/program/summaries", response_model=ProgramBarChartContent)
async def get_program_time_for_dashboard(dashboard_service: DashboardService = Depends(get_dashboard_service)):
    program_data = await dashboard_service.get_program_summary()
    if not isinstance(program_data, list):
        raise HTTPException(
            status_code=500, detail="Failed to retrieve program chart info")
    return ProgramBarChartContent(columns=manufacture_programs_bar_chart(program_data))


@app.get("/api/dashboard/chrome/summaries", response_model=ChromeBarChartContent)
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

@app.get("/api/dashboard/breakdown/week/{week_of}", response_model=ProductivityBreakdownByWeek)
async def get_productivity_breakdown(week_of: date = Path(..., description="Week starting date"),
                                     dashboard_service: DashboardService = Depends(get_dashboard_service)):
    weeks_overview: List[dict] = await dashboard_service.get_weekly_productivity_overview(UserLocalTime(week_of))
    if not isinstance(weeks_overview, list):
        raise HTTPException(
            status_code=500, detail="Failed to retrieve week of Chrome chart info")
    for some_dict in weeks_overview:
        if not isinstance(some_dict, dict):
            raise HTTPException(
                status_code=500, detail="Expected a list of dicts")

    return ProductivityBreakdownByWeek(days=DtoMapper.map_overview(weeks_overview))


@app.get("/api/dashboard/program/summaries/week", response_model=WeeklyProgramContent)
async def get_program_week_history(dashboard_service: DashboardService = Depends(get_dashboard_service)):
    week_of_data: List[DailyProgramSummary] = await dashboard_service.get_program_summary_weekly()
    if not isinstance(week_of_data, list):
        raise HTTPException(
            status_code=500, detail="Failed to retrieve week of program chart info")
    return WeeklyProgramContent(days=DtoMapper.map_programs(week_of_data))


@app.get("/api/dashboard/chrome/summaries/week", response_model=WeeklyChromeContent)
async def get_chrome_week_history(dashboard_service: DashboardService = Depends(get_dashboard_service)):
    week_of_unsorted_domain_summaries: List[DailyDomainSummary] = await dashboard_service.get_chrome_summary_weekly()

    if not isinstance(week_of_unsorted_domain_summaries, list):
        raise HTTPException(
            status_code=500, detail="Failed to retrieve week of Chrome chart info")
    for day in week_of_unsorted_domain_summaries:
        if not isinstance(day, DailyDomainSummary):
            raise HTTPException(
                status_code=500, detail="Did not receive a list of DailyDomainSummary objects")
    return WeeklyChromeContent(days=DtoMapper.map_chrome(week_of_unsorted_domain_summaries))


@app.get("/api/dashboard/chrome/summaries/week/{week_of}", response_model=WeeklyChromeContent)
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


@app.get("/api/dashboard/timeline/week", response_model=PartiallyPrecomputedWeeklyTimeline)
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

    return PartiallyPrecomputedWeeklyTimeline(beforeToday=rows, today=todays_payload, startDate=latest_sunday.dt)


@app.get("/api/dashboard/timeline/week/{week_of}", response_model=WeeklyTimeline)
async def get_previous_week_of_timeline(week_of: date = Path(..., description="Week starting date"),
                                        dashboard_service: DashboardService = Depends(get_dashboard_service)):
    days, start_of_week = await dashboard_service.get_specific_week_timeline(UserLocalTime(week_of))

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

    response = WeeklyTimeline(days=rows, start_date=start_of_week.dt)

    return response


@app.get("/api/dashboard/programs/usage/timeline", response_model=WeeklyProgramUsageTimeline)
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


@app.get("/api/dashboard/programs/usage/timeline/{week_of}", response_model=WeeklyProgramUsageTimeline)
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


@app.get("/api/report/chrome")
async def get_chrome_report(chrome_service: ChromeService = Depends(get_chrome_service)):
    logger.log_purple("[LOG] Get chrome tabs")
    # reports = await chrome_service.read_last_24_hrs()
    reports = None  # might be deprecated, this endpoint
    return reports


@app.post("/api/chrome/tab", status_code=status.HTTP_204_NO_CONTENT)
async def receive_chrome_tab(
    tab_change_event: UtcDtTabChange,
    chrome_service: ChromeService = Depends(get_chrome_service),
    timezone_service: TimezoneService = Depends(get_timezone_service)
):
    logger.log_purple("[LOG] Chrome Tab Received")
    try:
        utc_dt = tab_change_event.startTime.tzinfo == timezone.utc
        assert utc_dt, "Expected UTC datetime"

        user_id = 1  # temp until i have more than 1 user

        # NOTE: tab_change_event.startTime is in UTC at this point, a naive tz
        # capture_chrome_data_for_tests(tab_change_event)
        tz_for_user = timezone_service.get_tz_for_user(
            user_id)
        updated_tab_change_event = timezone_service.convert_tab_change_timezone(
            tab_change_event, tz_for_user)

        await chrome_service.tab_queue.add_to_arrival_queue(updated_tab_change_event)
        return  # Returns 204 No Content
    except AssertionError as e:
        print(f"Raw tzinfo: {tab_change_event.startTime.tzinfo}")
        print(e)  #
        raise HTTPException(
            status_code=400,
            detail="Expected a UTC-timezoned datetime"
        )
    except Exception as e:
        # print(e)
        # raise
        raise HTTPException(
            status_code=500,
            detail="A problem occurred in Chrome Service's tab endpoint"
        )


@app.post("/api/chrome/youtube", status_code=status.HTTP_204_NO_CONTENT)
async def receive_youtube_event(
    tab_change_event: YouTubeEvent,
    chrome_service: ChromeService = Depends(get_chrome_service),
    timezone_service: TimezoneService = Depends(get_timezone_service)
):
    logger.log_purple("[LOG] Chrome Tab Received")
    try:
        utc_dt = tab_change_event.startTime.tzinfo == timezone.utc
        assert utc_dt, "Expected UTC datetime"
        user_id = 1  # temp until i have more than 1 user

        # NOTE: tab_change_event.startTime is in UTC at this point, a naive tz
        # capture_chrome_data_for_tests(tab_change_event)
        tz_for_user = timezone_service.get_tz_for_user(
            user_id)
        updated_tab_change_event = timezone_service.convert_tab_change_timezone(
            tab_change_event, tz_for_user)

        await chrome_service.tab_queue.add_to_arrival_queue(updated_tab_change_event)
        return  # Returns 204 No Content
    except AssertionError as e:
        print(f"Raw tzinfo: {tab_change_event.startTime.tzinfo}")
        print(e)  #
        raise HTTPException(
            status_code=400,
            detail="Expected a UTC-timezoned datetime"
        )
    except Exception as e:
        # print(e)
        # raise
        raise HTTPException(
            status_code=500,
            detail="A problem occurred in Chrome Service's YouTube endpoint"
        )


@app.post("/api/chrome/ignored", status_code=status.HTTP_204_NO_CONTENT)
async def receive_ignored_tab(
    tab_change_event: UtcDtTabChange,
    chrome_service: ChromeService = Depends(get_chrome_service),
    timezone_service: TimezoneService = Depends(get_timezone_service)
):
    # Note that this is nigh identical to the other endpoint.
    # I diverge them early assuming they will have to diverge.
    logger.log_purple("[LOG] Ignored Chrome Tab Received")
    try:
        utc_dt = tab_change_event.startTime.tzinfo == timezone.utc
        assert utc_dt, "Expected UTC datetime"
        user_id = 1  # temp until i have more than 1 user

        # NOTE: tab_change_event.startTime is in UTC at this point, a naive tz
        # capture_chrome_data_for_tests(tab_change_event)
        tz_for_user = timezone_service.get_tz_for_user(
            user_id)
        updated_tab_change_event: TabChangeEventWithLtz = timezone_service.convert_tab_change_timezone(
            tab_change_event, tz_for_user)

        chrome_service.tab_queue.add_to_arrival_queue(updated_tab_change_event)
        return  # Returns 204 No Content
    except AssertionError as e:
        print(f"Raw tzinfo: {tab_change_event.startTime.tzinfo}")
        print(e)  #
        raise HTTPException(
            status_code=400,
            detail="Expected a UTC-timezoned datetime"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="A problem occurred in Chrome Service's Ignored Route"
        )

# TODO: Endpoint for the Camera stuff


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

