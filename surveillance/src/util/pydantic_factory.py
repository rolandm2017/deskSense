from src.object.pydantic_dto import KeyboardLog, MouseLog, ProgramActivityLog

from src.object.dto import TypingSessionDto, MouseMoveDto, ProgramDto

from src.db.models import DailyProgramSummary, DailyChromeSummary

from src.object.pydantic_dto import (
    DailyProgramSummarySchema,
    DailyChromeSummarySchema, WeeklyProgramContent, DayOfProgramContent

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
    return DailyProgramSummarySchema(id=v.id, programName=v.program_name, hoursSpent=v.hours_spent, gatheringDate=v.gathering_date)


def chrome_summary_row_to_pydantic(v: DailyChromeSummary):
    return DailyChromeSummarySchema(id=v.id, domainName=v.domain_name, hoursSpent=v.hours_spent, gatheringDate=v.gathering_date)


def manufacture_programs_bar_chart(program_data):
    return [program_summary_row_to_pydantic(r) for r in program_data]


def manufacture_chrome_bar_chart(program_data):
    return [chrome_summary_row_to_pydantic(r) for r in program_data]


def map_week_of_data_to_dto(week):
    out = []
    for day in week:
        day = DayOfProgramContent(
            date=day.date, content=manufacture_programs_bar_chart(day.columns))
        out.append(day)
    return out
