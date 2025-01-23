from src.object.pydantic_dto import KeyboardLog, MouseLog, ProgramActivityLog

from src.object.dto import TypingSessionDto, MouseMoveDto, ProgramDto


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
