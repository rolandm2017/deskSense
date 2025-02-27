# surveillance/src/service_dependencies.py
from fastapi import Depends
from typing import Callable
import asyncio

from surveillance.src.services.chrome_service import ChromeService
from surveillance.src.services.services import KeyboardService, MouseService, ProgramService

from .db.database import get_db, AsyncSession, async_session_maker
from .db.dao.mouse_dao import MouseDao
from .db.dao.keyboard_dao import KeyboardDao
from .db.dao.program_dao import ProgramDao
from .db.dao.timeline_entry_dao import TimelineEntryDao
from .db.dao.program_summary_dao import ProgramSummaryDao
from .db.dao.chrome_dao import ChromeDao
from .db.dao.chrome_summary_dao import ChromeSummaryDao
from .db.dao.summary_logs_dao import ProgramLoggingDao, ChromeLoggingDao
from .db.dao.video_dao import VideoDao
from .db.dao.frame_dao import FrameDao
from .arbiter.activity_arbiter import ActivityArbiter
from .util.clock import SystemClock


# Dependency functions
clock = SystemClock()


async def get_keyboard_dao() -> KeyboardDao:
    return KeyboardDao(clock, async_session_maker)


async def get_mouse_dao() -> MouseDao:
    return MouseDao(clock, async_session_maker)


async def get_program_dao() -> ProgramDao:
    return ProgramDao(clock, async_session_maker)


async def get_chrome_dao() -> ChromeDao:
    return ChromeDao(clock, async_session_maker)


async def get_timeline_dao() -> TimelineEntryDao:
    return TimelineEntryDao(clock, async_session_maker)


async def get_program_summary_dao() -> ProgramSummaryDao:
    program_logging_dao = ProgramLoggingDao(clock, async_session_maker)
    return ProgramSummaryDao(clock, program_logging_dao, async_session_maker)


async def get_chrome_summary_dao() -> ChromeSummaryDao:
    chrome_logging_dao = ChromeLoggingDao(clock, async_session_maker)
    return ChromeSummaryDao(clock, chrome_logging_dao, async_session_maker)


async def get_video_dao() -> VideoDao:
    return VideoDao(clock, async_session_maker)


async def get_frame_dao() -> FrameDao:
    return FrameDao(clock, async_session_maker)


async def get_keyboard_service(dao: KeyboardDao = Depends(get_keyboard_dao)) -> KeyboardService:
    from .services.services import KeyboardService
    return KeyboardService(dao)

# async def get_keyboard_service(dao: KeyboardDao = Depends(KeyboardDao)) -> Callable:
    # Lazy import to avoid circular dependency
    # from .services import KeyboardService
    # return KeyboardService(dao)


async def get_mouse_service(dao: MouseDao = Depends(get_mouse_dao)) -> MouseService:
    # Lazy import to avoid circular dependency
    from .services.services import MouseService
    return MouseService(dao)


async def get_program_service(dao: ProgramDao = Depends(get_program_dao)) -> ProgramService:
    # Lazy import to avoid circular dependency
    from .services.services import ProgramService
    return ProgramService(dao)


async def get_dashboard_service(
    timeline_dao: TimelineEntryDao = Depends(get_timeline_dao),
    program_summary_dao: ProgramSummaryDao = Depends(get_program_summary_dao),
    chrome_summary_dao: ChromeSummaryDao = Depends(get_chrome_summary_dao)
):
    # Lazy import to avoid circular dependency
    from .services.dashboard_service import DashboardService
    return DashboardService(timeline_dao, program_summary_dao, chrome_summary_dao)


# Singleton instance of ActivityArbiter
_arbiter_instance = None
# Singleton instance of ChromeService
_chrome_service_instance = None


async def get_activity_arbiter():
    from .debug.debug_overlay import Overlay
    from .arbiter.activity_arbiter import ActivityArbiter
    from .db.dao.program_summary_dao import ProgramSummaryDao
    from .db.dao.chrome_summary_dao import ChromeSummaryDao

    loop = asyncio.get_event_loop()
    clock = SystemClock()
    chrome_logging_dao = ChromeLoggingDao(clock, async_session_maker)
    program_logging_dao = ProgramLoggingDao(clock, async_session_maker)
    # print("Starting get_activity_arbiter")

    global _arbiter_instance
    if not _arbiter_instance:
        print("Creating new Overlay")
        overlay = Overlay()
        print("Creating new ActivityArbiter")
        chrome_service = await get_chrome_service()

        _arbiter_instance = ActivityArbiter(
            overlay=overlay,
            clock=clock,
            chrome_summary_dao=ChromeSummaryDao(
                clock, chrome_logging_dao, async_session_maker),
            program_summary_dao=ProgramSummaryDao(
                clock, program_logging_dao, async_session_maker)
        )

        # Create wrapper for async handler
        @chrome_service.event_emitter.on('tab_change')
        def handle_tab_change(tab):
            # Create and schedule the task
            if _arbiter_instance is None:
                raise ValueError("Arbiter instance should be set by now")
            loop.create_task(_arbiter_instance.set_tab_state(tab))

        print("ActivityArbiter created successfully")
    # else:
        # print(f"Reusing arbiter instance with id: {id(_arbiter_instance)}")

    return _arbiter_instance


async def get_chrome_service(dao: ChromeDao = Depends(get_chrome_dao),
                             arbiter: ActivityArbiter = Depends(get_activity_arbiter)) -> ChromeService:
    # Lazy import to avoid circular dependency
    from .services.chrome_service import ChromeService
    global _chrome_service_instance  # Singleton because it must preserve internal state
    if _chrome_service_instance is None:
        clock = SystemClock()
        _chrome_service_instance = ChromeService(clock,
                                                 arbiter,
                                                 dao=ChromeDao(
                                                     clock, async_session_maker)

                                                 )
    return _chrome_service_instance


async def get_video_service(video_dao: VideoDao = Depends(get_video_dao), frame_dao: FrameDao = Depends(get_frame_dao)):
    from .services.services import VideoService
    return VideoService(video_dao, frame_dao)
