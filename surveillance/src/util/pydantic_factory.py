from typing import List

from src.object.pydantic_dto import KeyboardLog, MouseLog, ProgramActivityLog
from src.object.dto import TypingSessionDto, MouseMoveDto, ProgramDto

from src.db.models import DailyProgramSummary, DailyDomainSummary

from src.object.dashboard_dto import (
    ProductivityBreakdown, DailyProgramSummarySchema, DailyDomainSummarySchema,
    WeeklyProgramContent,
    DayOfProgramContent, DayOfChromeContent,
    ChromeBarChartContent, ProgramBarChartContent

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
            productive=r.productive if r.productive else False
        )
    except AttributeError as e:
        raise e


def program_summary_row_to_pydantic(v: DailyProgramSummary):
    return DailyProgramSummarySchema.model_validate(v)
    # return DailyProgramSummarySchema(
    #     id=v.id,  # type: ignore
    #     programName=v.program_name,  # type: ignore
    #     hoursSpent=v.hours_spent,  # type: ignore
    #     gatheringDate=v.gathering_date  # type: ignore
    # )  # type: ignore


def chrome_summary_row_to_pydantic(v: DailyDomainSummary):
    return DailyDomainSummarySchema.model_validate(v)
    # return DailyDomainSummarySchema(id=v.id, domainName=v.domain_name, hoursSpent=v.hours_spent, gatheringDate=v.gathering_date)


def manufacture_programs_bar_chart(program_data: List[DailyProgramSummary]):
    return [program_summary_row_to_pydantic(r) for r in program_data]


def manufacture_chrome_bar_chart(chrome_data: List[DailyDomainSummary]):
    return [chrome_summary_row_to_pydantic(r) for r in chrome_data]


class DtoMapper:
    def __init__(self):
        pass

    @staticmethod
    def map_programs(week):
        return map_week_of_program_data_to_dto(week)

    @staticmethod
    def map_chrome(week: List[DailyDomainSummary]):
        return map_week_of_chrome_data_to_dto(week)

    @staticmethod
    def map_overview(week: List[dict]):
        return map_week_of_overviews_to_dto(week)


def map_week_of_overviews_to_dto(unsorted_week: List[dict]) -> List[ProductivityBreakdown]:
    out = [ProductivityBreakdown(day=d["day"],
                                 productiveHours=d["productivity"],
                                 leisureHours=d["leisure"]) for d in unsorted_week]
    return out


def map_week_of_program_data_to_dto(unsorted_week: List[DailyProgramSummary]):
    out = []
    grouped_by_day = {}

    for domain_report in unsorted_week:
        assert isinstance(domain_report, DailyProgramSummary)
        day = domain_report.gathering_date.date()
        if day in grouped_by_day:
            grouped_by_day[day].append(domain_report)
        else:
            grouped_by_day[day] = [domain_report]
    for day, reports in grouped_by_day.items():
        content = [program_summary_row_to_pydantic(r) for r in reports]
        bar_chart_content = ProgramBarChartContent(columns=content)
        day = DayOfProgramContent(date=day, content=bar_chart_content)
        out.append(day)
    return out


def map_week_of_chrome_data_to_dto(unsorted_week: List[DailyDomainSummary]):
    out = []
    grouped_by_day = {}

    for domain_report in unsorted_week:
        assert isinstance(domain_report, DailyDomainSummary)
        day = domain_report.gathering_date.date()
        if day in grouped_by_day:
            grouped_by_day[day].append(domain_report)
        else:
            grouped_by_day[day] = [domain_report]
    for day, reports in grouped_by_day.items():
        content = [
            chrome_summary_row_to_pydantic(r) for r in reports]
        bar_chart_content = ChromeBarChartContent(columns=content)
        day = DayOfChromeContent(
            date=day, content=bar_chart_content)
        out.append(day)
    return out
