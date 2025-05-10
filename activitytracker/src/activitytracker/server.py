# server.py
import os
import sys
from contextlib import asynccontextmanager

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Path,
    Request,
    status,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import asyncio

import pytz
from datetime import date, datetime
from datetime import time as dt_time
from datetime import timezone
from time import time

# import time
from typing import List, Optional

from activitytracker.db.database import (
    async_session_maker,
    init_db,
    regular_session_maker,
)
from activitytracker.db.models import (
    DailyDomainSummary,
    DailyProgramSummary,
    ProgramSummaryLog,
)
from activitytracker.facade.facade_singletons import (
    get_keyboard_facade_instance,
    get_mouse_facade_instance,
)
from activitytracker.facade.receive_messages import MessageReceiver
from activitytracker.object.classes import TabChangeEventWithLtz
from activitytracker.object.dashboard_dto import (
    ChromeBarChartContent,
    DayOfTimelineRows,
    PartiallyPrecomputedWeeklyTimeline,
    ProductivityBreakdownByWeek,
    ProgramBarChartContent,
    ProgramTimelineContent,
    ProgramUsageTimeline,
    TimelineEntrySchema,
    TimelineEvent,
    TimelineRows,
    WeeklyChromeContent,
    WeeklyProgramContent,
    WeeklyProgramUsageTimeline,
    WeeklyTimeline,
)
from activitytracker.object.pydantic_dto import (
    UtcDtTabChange,
    YouTubePlayerChange,
    YouTubeTabChange,
)
from activitytracker.routes.report_routes import router as report_router
from activitytracker.service_dependencies import (
    get_activity_arbiter,
    get_chrome_service,
    get_dashboard_service,
    get_keyboard_service,
    get_mouse_service,
    get_timezone_service,
)
from activitytracker.services.chrome_service import ChromeService
from activitytracker.services.dashboard_service import DashboardService
from activitytracker.services.tiny_services import TimezoneService
from activitytracker.surveillance_manager import FacadeInjector, SurveillanceManager
from activitytracker.util.clock import UserFacingClock
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.errors import MustHaveUtcTzInfoError
from activitytracker.util.pydantic_factory import (
    DtoMapper,
    manufacture_chrome_bar_chart,
    manufacture_programs_bar_chart,
)
from activitytracker.util.time_wrappers import UserLocalTime

# from activitytracker.facade.program_facade import ProgramApiFacadeCore


# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), "w", buffering=1)
print("SERVER STARTING WITH UNBUFFERED OUTPUT")

logger = ConsoleLogger()


# Main class in this file
class ActivityTrackerState:
    def __init__(self):
        self.manager: Optional[SurveillanceManager] = None
        self.tracking_task: Optional[asyncio.Task] = None
        self.is_running: bool = False
        self.db_session = None


activity_tracker_state = ActivityTrackerState()


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
            from activitytracker.facade.program_facade_windows import (
                WindowsProgramFacadeCore,
            )

            return WindowsProgramFacadeCore()
        else:
            from activitytracker.facade.program_facade_ubuntu import (
                UbuntuProgramFacadeCore,
            )

            return UbuntuProgramFacadeCore()

    facades = FacadeInjector(
        get_keyboard_facade_instance, get_mouse_facade_instance, choose_program_facade
    )

    message_receiver = MessageReceiver("tcp://127.0.0.1:5555")
    activity_tracker_state.manager = SurveillanceManager(
        user_facing_clock,
        async_session_maker,
        regular_session_maker,
        chrome_service,
        arbiter,
        facades,
        message_receiver,
    )
    activity_tracker_state.manager.print_sys_status_info()
    activity_tracker_state.manager.start_trackers()

    try:
        yield
    finally:
        # Shutdown
        activity_tracker_state.is_running = False

        print("Shutting down productivity tracking...")
        if activity_tracker_state.manager:
            try:
                # Use a timeout to ensure cleanup doesn't hang
                cancelled_count = await asyncio.wait_for(
                    activity_tracker_state.manager.cleanup(), timeout=5.0
                )
                print(f"Cleanup complete. Total tasks cancelled: {cancelled_count}")

                # Also ensure the shutdown handler runs
                activity_tracker_state.manager.shutdown_handler()
            except asyncio.CancelledError as ce:
                print(
                    "Cleanup itself was cancelled - this is likely from the web server shutting down"
                )
                # Still try to run the shutdown handler
                try:
                    activity_tracker_state.manager.shutdown_handler()
                except Exception:
                    pass
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


class HealthResponse(BaseModel):
    status: str
    detail: str | None = None


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    logger.log_purple("[LOG] health check")
    try:
        if (
            not activity_tracker_state
            and not activity_tracker_state.manager.keyboard_tracker
        ):
            return {"status": "error", "detail": "Tracker not initialized"}
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print("VALIDATION ERROR:", exc.errors())
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.get("/api/dashboard/timeline", response_model=TimelineRows)
async def get_timeline_for_dashboard(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    # mouse_rows, keyboard_rows = await dashboard_service.get_peripheral_timeline_for_today()
    mouse_rows, keyboard_rows = await dashboard_service.peripherals.get_timeline_for_today()
    # // TODO: make this be given by day
    if not isinstance(mouse_rows, list) or not isinstance(keyboard_rows, list):
        raise HTTPException(status_code=500, detail="Failed to retrieve timeline info")

    # Convert SQLAlchemy models to Pydantic models
    pydantic_mouse_rows = [TimelineEntrySchema.from_orm_model(row) for row in mouse_rows]
    pydantic_keyboard_rows = [
        TimelineEntrySchema.from_orm_model(row) for row in keyboard_rows
    ]

    return TimelineRows(mouseRows=pydantic_mouse_rows, keyboardRows=pydantic_keyboard_rows)


@app.get("/api/dashboard/program/summaries", response_model=ProgramBarChartContent)
async def get_program_time_for_dashboard(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    program_data = await dashboard_service.get_program_summary()
    if not isinstance(program_data, list):
        raise HTTPException(status_code=500, detail="Failed to retrieve program chart info")
    return ProgramBarChartContent(columns=manufacture_programs_bar_chart(program_data))


@app.get("/api/dashboard/chrome/summaries", response_model=ChromeBarChartContent)
async def get_chrome_time_for_dashboard(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    chrome_data = await dashboard_service.get_chrome_summary()
    if not isinstance(chrome_data, list):
        raise HTTPException(status_code=500, detail="Failed to retrieve Chrome chart info")
    return ChromeBarChartContent(columns=manufacture_chrome_bar_chart(chrome_data))


#
# By Week # By Week
# By Week # By Week # By Week
# By Week # By Week
#


@app.get(
    "/api/dashboard/breakdown/week/{week_of}", response_model=ProductivityBreakdownByWeek
)
async def get_productivity_breakdown(
    week_of: date = Path(..., description="Week starting date"),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
    timezone_service: TimezoneService = Depends(get_timezone_service),
):
    weeks_overview: List[dict] = await dashboard_service.get_weekly_productivity_overview(
        week_of
    )
    if not isinstance(weeks_overview, list):
        raise HTTPException(
            status_code=500, detail="Failed to retrieve week of Chrome chart info"
        )
    for some_dict in weeks_overview:
        if not isinstance(some_dict, dict):
            raise HTTPException(status_code=500, detail="Expected a list of dicts")

    return ProductivityBreakdownByWeek(days=DtoMapper.map_overview(weeks_overview))


@app.get("/api/dashboard/program/summaries/week", response_model=WeeklyProgramContent)
async def get_program_week_history(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    week_of_data: List[DailyProgramSummary] = (
        await dashboard_service.get_program_summary_weekly()
    )
    if not isinstance(week_of_data, list):
        raise HTTPException(
            status_code=500, detail="Failed to retrieve week of program chart info"
        )
    return WeeklyProgramContent(days=DtoMapper.map_programs(week_of_data))


@app.get("/api/dashboard/chrome/summaries/week", response_model=WeeklyChromeContent)
async def get_chrome_week_history(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    week_of_unsorted_domain_summaries: List[DailyDomainSummary] = (
        await dashboard_service.get_chrome_summary_weekly()
    )

    if not isinstance(week_of_unsorted_domain_summaries, list):
        raise HTTPException(
            status_code=500, detail="Failed to retrieve week of Chrome chart info"
        )
    for day in week_of_unsorted_domain_summaries:
        if not isinstance(day, DailyDomainSummary):
            raise HTTPException(
                status_code=500,
                detail="Did not receive a list of DailyDomainSummary objects",
            )
    return WeeklyChromeContent(days=DtoMapper.map_chrome(week_of_unsorted_domain_summaries))


@app.get(
    "/api/dashboard/chrome/summaries/week/{week_of}", response_model=WeeklyChromeContent
)
async def get_previous_week_chrome_history(
    week_of: date = Path(..., description="Week starting date"),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    week_of_unsorted_domain_summaries: List[DailyDomainSummary] = (
        await dashboard_service.get_previous_week_chrome_summary(week_of)
    )

    if not isinstance(week_of_unsorted_domain_summaries, list):
        raise HTTPException(
            status_code=500, detail="Failed to retrieve week of Chrome chart info"
        )

    # Is a list of lists
    for day in week_of_unsorted_domain_summaries:
        if not isinstance(day, DailyDomainSummary):
            raise HTTPException(
                status_code=500,
                detail="Did not receive a list of Daily Domain Summaries, received instead:"
                + str(type(day)),
            )

    # days = [DtoMapper.map_chrome(day) for day in package]
    days = DtoMapper.map_chrome(week_of_unsorted_domain_summaries)

    return WeeklyChromeContent(days=days)


@app.get("/api/dashboard/timeline/week", response_model=PartiallyPrecomputedWeeklyTimeline)
async def get_timeline_weekly(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    days_before_today, todays_payload, latest_sunday = (
        await dashboard_service.peripherals.get_current_week_timeline()
    )
    rows: List[DayOfTimelineRows] = []

    assert isinstance(todays_payload, dict)
    todays_date = todays_payload["date"]

    mouse_rows = todays_payload["mouse_events"]
    keyboard_rows = todays_payload["keyboard_events"]
    # Convert SQLAlchemy models to Pydantic models
    pydantic_mouse_rows = [TimelineEntrySchema.from_orm_model(row) for row in mouse_rows]
    pydantic_keyboard_rows = [
        TimelineEntrySchema.from_orm_model(row) for row in keyboard_rows
    ]

    todays_row = TimelineRows(
        mouseRows=pydantic_mouse_rows, keyboardRows=pydantic_keyboard_rows
    )

    todays_payload = DayOfTimelineRows(date=todays_date, row=todays_row)

    for day in days_before_today:
        assert isinstance(day, dict)
        mouse_rows = day["mouse_events"]
        keyboard_rows = day["keyboard_events"]
        # Convert SQLAlchemy models to Pydantic models
        pydantic_mouse_rows = [TimelineEntrySchema.from_orm_model(row) for row in mouse_rows]
        pydantic_keyboard_rows = [
            TimelineEntrySchema.from_orm_model(row) for row in keyboard_rows
        ]

        row = TimelineRows(
            mouseRows=pydantic_mouse_rows, keyboardRows=pydantic_keyboard_rows
        )

        row = DayOfTimelineRows(date=day["date"], row=row)
        rows.append(row)

    if not isinstance(latest_sunday, datetime):
        raise ValueError("Expected dt in latest_sunday")

    return PartiallyPrecomputedWeeklyTimeline(
        beforeToday=rows, today=todays_payload, startDate=latest_sunday
    )


@app.get("/api/dashboard/timeline/week/{week_of}", response_model=WeeklyTimeline)
async def get_previous_week_of_timeline(
    week_of: date = Path(..., description="Week starting date"),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):

    days, start_of_week = await dashboard_service.peripherals.get_specific_week_timeline(
        week_of
    )

    if not isinstance(start_of_week, datetime):
        raise ValueError("start_of_week.dt was expected to be a datetime")

    rows: List[DayOfTimelineRows] = []
    for day in days:
        assert isinstance(day, dict)
        mouse_rows = day["mouse_events"]
        keyboard_rows = day["keyboard_events"]

        pydantic_mouse_rows = [TimelineEntrySchema.from_orm_model(row) for row in mouse_rows]
        pydantic_keyboard_rows = [
            TimelineEntrySchema.from_orm_model(row) for row in keyboard_rows
        ]
        row = TimelineRows(
            mouseRows=pydantic_mouse_rows, keyboardRows=pydantic_keyboard_rows
        )
        row = DayOfTimelineRows(date=day["date"], row=row)
        rows.append(row)

    # TODO: Convert from UTC to PST for the client
    appeasement_of_type_checker = datetime.combine(
        start_of_week.date(), start_of_week.time(), start_of_week.tzinfo
    )

    response = WeeklyTimeline(days=rows, start_date=appeasement_of_type_checker)

    return response


@app.get("/api/dashboard/programs/usage/timeline", response_model=WeeklyProgramUsageTimeline)
async def get_program_usage_timeline_for_present_week(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    all_days, start_of_week = (
        await dashboard_service.programs.get_current_week_usage_timeline()
    )

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
                    logId=program_log.id,
                    startTime=program_log.start_time,
                    endTime=program_log.end_time,
                )
                timeline_events.append(timeline_event)

            content = ProgramTimelineContent(programName=key, events=timeline_events)
            programs_content.append(content)
        day_timeline = ProgramUsageTimeline(date=date, programs=programs_content)
        days.append(day_timeline)

        # program_timeline_content = ProgramTimelineContent(programName=)
        # program_usage_timeline = ProgramUsageTimeline(date=date, programs=package=[''])
    return WeeklyProgramUsageTimeline(days=days)


@app.get(
    "/api/dashboard/programs/usage/timeline/{week_of}",
    response_model=WeeklyProgramUsageTimeline,
)
async def get_program_usage_timeline_by_week(
    week_of: date = Path(..., description="Week starting date"),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):

    all_days, start_of_week = await dashboard_service.programs.get_usage_timeline_for_week(
        week_of
    )

    days = []
    for day in all_days:
        programs: dict[str, ProgramSummaryLog] = day["program_usage_timeline"]
        date = day["date"]

        programs_content = []
        for key, value_list in programs.items():
            timeline_events = []
            for program_log in value_list:
                timeline_event = TimelineEvent(
                    logId=program_log.id,
                    startTime=program_log.start_time,
                    endTime=program_log.end_time,
                )
                timeline_events.append(timeline_event)

            content = ProgramTimelineContent(programName=key, events=timeline_events)
            programs_content.append(content)

        day_timeline = ProgramUsageTimeline(date=date, programs=programs_content)
        days.append(day_timeline)

    return WeeklyProgramUsageTimeline(days=days)


@app.get("/api/report/chrome")
async def get_chrome_report(chrome_service: ChromeService = Depends(get_chrome_service)):
    logger.log_purple("[LOG] Get chrome tabs")
    # reports = await chrome_service.read_last_24_hrs()
    reports = None  # might be deprecated, this endpoint
    return reports


def field_has_utc_tzinfo_else_throw(start_time_field):
    utc_dt = start_time_field.tzinfo == timezone.utc
    if not utc_dt:
        raise MustHaveUtcTzInfoError()


@app.post("/api/chrome/tab", status_code=status.HTTP_204_NO_CONTENT)
async def receive_chrome_tab(
    tab_change_event: UtcDtTabChange,
    chrome_service: ChromeService = Depends(get_chrome_service),
    timezone_service: TimezoneService = Depends(get_timezone_service),
):
    logger.log_purple("[LOG] Chrome Tab Received")
    try:
        field_has_utc_tzinfo_else_throw(tab_change_event)
        user_id = 1  # temp until i have more than 1 user

        # NOTE: tab_change_event.startTime is in UTC at this point, a naive tz
        # capture_chrome_data_for_tests(tab_change_event)
        tz_for_user = timezone_service.get_tz_for_user(user_id)
        updated_tab_change_event: TabChangeEventWithLtz = (
            timezone_service.convert_tab_change_timezone(tab_change_event, tz_for_user)
        )

        chrome_service.tab_queue.add_to_arrival_queue(updated_tab_change_event)
        return  # Returns 204 No Content
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500, detail="A problem occurred in Chrome Service's tab endpoint"
        )


@app.post("/api/chrome/youtube/new", status_code=status.HTTP_204_NO_CONTENT)
async def receive_youtube_event(
    tab_change_event: YouTubeTabChange,
    chrome_service: ChromeService = Depends(get_chrome_service),
    timezone_service: TimezoneService = Depends(get_timezone_service),
):
    logger.log_purple("[LOG] Chrome Tab Received")
    try:
        print(
            f"received {tab_change_event.pageEvent.channel} with id {tab_change_event.pageEvent.videoId}"
        )
        field_has_utc_tzinfo_else_throw(tab_change_event.startTime)

        user_id = 1  # temp until i have more than 1 user

        # NOTE: tab_change_event.startTime is in UTC at this point, a naive tz
        # capture_chrome_data_for_tests(tab_change_event)
        tz_for_user = timezone_service.get_tz_for_user(user_id)
        updated_tab_change_event: TabChangeEventWithLtz = (
            timezone_service.convert_tz_for_youtube_tab_change(tab_change_event, tz_for_user)
        )

        chrome_service.tab_queue.add_to_arrival_queue(updated_tab_change_event)
        return  # Returns 204 No Content
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500, detail="A problem occurred in Chrome Service's YouTube endpoint"
        )


@app.post("/api/chrome/youtube/state", status_code=status.HTTP_204_NO_CONTENT)
async def receive_youtube_player_state(
    tab_change_event: YouTubePlayerChange,
    chrome_service: ChromeService = Depends(get_chrome_service),
    timezone_service: TimezoneService = Depends(get_timezone_service),
):
    logger.log_purple("[LOG] Chrome Tab Received")
    try:
        print("State received", tab_change_event.playerEvent.playerState)
        field_has_utc_tzinfo_else_throw(tab_change_event.startTime)
        user_id = 1  # temp until i have more than 1 user

        # NOTE: tab_change_event.startTime is in UTC at this point, a naive tz
        # capture_chrome_data_for_tests(tab_change_event)
        tz_for_user = timezone_service.get_tz_for_user(user_id)

        # TODO: One way to solve getting the YouTubeEvent into the Arbiter,
        # is to attach it to a ChromeSession, because well, it is a chrome session.
        # And then assume that the transit makes it through OK.
        updated_tab_change_event: TabChangeEventWithLtz = (
            timezone_service.convert_tz_for_youtube_state_change(
                tab_change_event, tz_for_user
            )
        )

        chrome_service.tab_queue.add_to_arrival_queue(updated_tab_change_event)
        return  # Returns 204 No Content
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500, detail="A problem occurred in Chrome Service's YouTube endpoint"
        )


@app.post("/api/chrome/ignored", status_code=status.HTTP_204_NO_CONTENT)
async def receive_ignored_tab(
    tab_change_event: UtcDtTabChange,
    chrome_service: ChromeService = Depends(get_chrome_service),
    timezone_service: TimezoneService = Depends(get_timezone_service),
):
    # Note that this is nigh identical to the other endpoint.
    # I diverge them early assuming they will have to diverge.
    logger.log_purple("[LOG] Ignored Chrome Tab Received")
    try:
        field_has_utc_tzinfo_else_throw(tab_change_event.startTime)
        user_id = 1  # temp until i have more than 1 user

        # NOTE: tab_change_event.startTime is in UTC at this point, a naive tz
        # capture_chrome_data_for_tests(tab_change_event)
        tz_for_user = timezone_service.get_tz_for_user(user_id)
        updated_tab_change_event: TabChangeEventWithLtz = (
            timezone_service.convert_tab_change_timezone(tab_change_event, tz_for_user)
        )

        chrome_service.tab_queue.add_to_arrival_queue(updated_tab_change_event)
        return  # Returns 204 No Content
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="A problem occurred in Chrome Service's Ignored Route"
        )


# TODO: Endpoint for the Camera stuff


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
