# surveillance/src/service_dependencies.py
from fastapi import Depends
from typing import Callable

from .db.database import get_db, AsyncSession, async_session_maker
from .db.dao.mouse_dao import MouseDao
from .db.dao.keyboard_dao import KeyboardDao
from .db.dao.program_dao import ProgramDao
from .db.dao.timeline_entry_dao import TimelineEntryDao
from .db.dao.program_summary_dao import ProgramSummaryDao
from .db.dao.chrome_dao import ChromeDao
from .db.dao.chrome_summary_dao import ChromeSummaryDao
from .db.dao.video_dao import VideoDao
from .db.dao.frame_dao import FrameDao
from .arbiter.activity_arbiter import ActivityArbiter
from .debug.claude_overlay_v2 import Overlay


# Dependency functions

async def get_keyboard_dao() -> KeyboardDao:
    return KeyboardDao(async_session_maker)


async def get_mouse_dao() -> MouseDao:
    return MouseDao(async_session_maker)


async def get_program_dao() -> ProgramDao:
    return ProgramDao(async_session_maker)


async def get_chrome_dao() -> ChromeDao:
    return ChromeDao(async_session_maker)


async def get_timeline_dao() -> TimelineEntryDao:
    return TimelineEntryDao(async_session_maker)


async def get_program_summary_dao() -> ProgramSummaryDao:
    return ProgramSummaryDao(async_session_maker)


async def get_chrome_summary_dao() -> ChromeSummaryDao:
    return ChromeSummaryDao(async_session_maker)


async def get_video_dao() -> VideoDao:
    return VideoDao(async_session_maker)


async def get_frame_dao() -> FrameDao:
    return FrameDao(async_session_maker)


async def get_keyboard_service(dao: KeyboardDao = Depends(get_keyboard_dao)) -> Callable:
    from .services.services import KeyboardService
    return KeyboardService(dao)

# async def get_keyboard_service(dao: KeyboardDao = Depends(KeyboardDao)) -> Callable:
    # Lazy import to avoid circular dependency
    # from .services import KeyboardService
    # return KeyboardService(dao)


async def get_mouse_service(dao: MouseDao = Depends(get_mouse_dao)) -> Callable:
    # Lazy import to avoid circular dependency
    from .services.services import MouseService
    return MouseService(dao)


async def get_program_service(dao: ProgramDao = Depends(get_program_dao)) -> Callable:
    # Lazy import to avoid circular dependency
    from .services.services import ProgramService
    return ProgramService(dao)


async def get_dashboard_service(
    timeline_dao: TimelineEntryDao = Depends(get_timeline_dao),
    program_summary_dao: ProgramSummaryDao = Depends(get_program_summary_dao),
    chrome_summary_dao: ChromeSummaryDao = Depends(get_chrome_summary_dao)
) -> Callable:
    # Lazy import to avoid circular dependency
    from .services.dashboard_service import DashboardService
    return DashboardService(timeline_dao, program_summary_dao, chrome_summary_dao)

# Singleton instance of ChromeService
_chrome_service_instance = None


async def get_chrome_service(dao: ChromeDao = Depends(get_chrome_dao),
                             summary_dao: ChromeSummaryDao = Depends(get_chrome_summary_dao)) -> Callable:
    # Lazy import to avoid circular dependency
    from .services.chrome_service import ChromeService
    global _chrome_service_instance  # Singleton because it must preserve internal state
    if _chrome_service_instance is None:
        # TODO: Initialize display
        magic_fraps_overlay = Overlay()
        arbiter = ActivityArbiter(magic_fraps_overlay)
        _chrome_service_instance = ChromeService(
            arbiter,
            dao=ChromeDao(async_session_maker),
            summary_dao=ChromeSummaryDao(async_session_maker)
        )
    return _chrome_service_instance


# async def get_chrome_service(
#     dao: ChromeDao = Depends(get_chrome_dao),
#     summary_dao: ChromeSummaryDao = Depends(get_chrome_summary_dao)
# ) -> Callable:
#     from .services import ChromeService  # Lazy import to avoid circular dependency
#     return ChromeService(dao, summary_dao)

async def get_video_service(video_dao: VideoDao = Depends(get_video_dao), frame_dao: FrameDao = Depends(get_frame_dao)):
    from .services.services import VideoService
    return VideoService(video_dao, frame_dao)
