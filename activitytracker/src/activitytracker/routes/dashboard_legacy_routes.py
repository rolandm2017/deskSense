from datetime import date, datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path

from activitytracker.db.models import (
    DailyDomainSummary,
    DailyProgramSummary,
    ProgramActivityLog,
)
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
from activitytracker.service_dependencies import (
    get_dashboard_service,
    get_timezone_service,
)
from activitytracker.services.dashboard_service import DashboardService
from activitytracker.services.timezone_service import TimezoneService
from activitytracker.util.pydantic_factory import (
    DtoMapper,
    manufacture_chrome_bar_chart,
    manufacture_programs_bar_chart,
)


router = APIRouter(
    prefix="/api/dashboard",
    tags=["dashboard-legacy"],
    deprecated=True,
)


@router.get("/timeline", response_model=TimelineRows)
async def get_timeline_for_dashboard(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    mouse_rows, keyboard_rows = await dashboard_service.peripherals.get_timeline_for_today()
    # TODO: make this be given by day
    if not isinstance(mouse_rows, list) or not isinstance(keyboard_rows, list):
        raise HTTPException(status_code=500, detail="Failed to retrieve timeline info")

    pydantic_mouse_rows = [TimelineEntrySchema.from_orm_model(row) for row in mouse_rows]
    pydantic_keyboard_rows = [
        TimelineEntrySchema.from_orm_model(row) for row in keyboard_rows
    ]

    return TimelineRows(mouseRows=pydantic_mouse_rows, keyboardRows=pydantic_keyboard_rows)


@router.get("/program/summaries", response_model=ProgramBarChartContent)
async def get_program_time_for_dashboard(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    program_data = await dashboard_service.get_program_summary()
    if not isinstance(program_data, list):
        raise HTTPException(status_code=500, detail="Failed to retrieve program chart info")
    return ProgramBarChartContent(columns=manufacture_programs_bar_chart(program_data))


@router.get("/chrome/summaries", response_model=ChromeBarChartContent)
async def get_chrome_time_for_dashboard(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    print("in the rome/summarie endpoint 283rm")
    chrome_data = await dashboard_service.get_chrome_summary()
    if not isinstance(chrome_data, list):
        raise HTTPException(status_code=500, detail="Failed to retrieve Chrome chart info")
    return ChromeBarChartContent(columns=manufacture_chrome_bar_chart(chrome_data))


@router.get("/breakdown/week/{week_of}", response_model=ProductivityBreakdownByWeek)
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


@router.get("/program/summaries/week", response_model=WeeklyProgramContent)
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


@router.get("/chrome/summaries/week", response_model=WeeklyChromeContent)
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


@router.get("/chrome/summaries/week/{week_of}", response_model=WeeklyChromeContent)
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

    for day in week_of_unsorted_domain_summaries:
        if not isinstance(day, DailyDomainSummary):
            raise HTTPException(
                status_code=500,
                detail="Did not receive a list of Daily Domain Summaries, received instead:"
                + str(type(day)),
            )

    days = DtoMapper.map_chrome(week_of_unsorted_domain_summaries)

    return WeeklyChromeContent(days=days)


@router.get("/timeline/week", response_model=PartiallyPrecomputedWeeklyTimeline)
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


@router.get("/timeline/week/{week_of}", response_model=WeeklyTimeline)
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


@router.get("/programs/usage/timeline", response_model=WeeklyProgramUsageTimeline)
async def get_program_usage_timeline_for_present_week(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    all_days, start_of_week = (
        await dashboard_service.programs.get_current_week_usage_timeline()
    )

    days = []
    for day in all_days:
        programs: dict[str, ProgramActivityLog] = day["program_usage_timeline"]
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


@router.get(
    "/programs/usage/timeline/{week_of}",
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
        programs: dict[str, ProgramActivityLog] = day["program_usage_timeline"]
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
