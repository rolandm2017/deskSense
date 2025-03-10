# surveillance/src/service_dependencies.py
from .util.clock import SystemClock, UserFacingClock
from fastapi import Depends
from typing import Callable
import asyncio


from .debug.ui_notifier import UINotifier

from .services.chrome_service import ChromeService
from .services.services import KeyboardService, MouseService, ProgramService, TimezoneService

from .db.database import async_session_maker
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
from .arbiter.activity_recorder import ActivityRecorder


# Dependency functions
system_clock = SystemClock()
user_facing_clock = UserFacingClock()

_program_logging_dao = ProgramLoggingDao(async_session_maker)
_chrome_logging_dao = ChromeLoggingDao(async_session_maker)


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
    # program_logging_dao = ProgramLoggingDao(async_session_maker)
    return ProgramSummaryDao(_program_logging_dao, async_session_maker)


async def get_chrome_summary_dao() -> ChromeSummaryDao:
    # chrome_logging_dao = ChromeLoggingDao(async_session_maker)
    return ChromeSummaryDao(_chrome_logging_dao, async_session_maker)


async def get_program_logging_dao() -> ProgramLoggingDao:
    return _program_logging_dao


async def get_chrome_logging_dao() -> ChromeLoggingDao:
    return _chrome_logging_dao


async def get_video_dao() -> VideoDao:
    return VideoDao(async_session_maker)


async def get_frame_dao() -> FrameDao:
    return FrameDao(async_session_maker)


async def get_timezone_service() -> TimezoneService:
    from .services.services import TimezoneService
    return TimezoneService()


async def get_keyboard_service(dao: KeyboardDao = Depends(get_keyboard_dao)) -> KeyboardService:
    from .services.services import KeyboardService
    return KeyboardService(dao)


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
    program_logging_dao: ProgramLoggingDao = Depends(get_program_logging_dao),
    chrome_summary_dao: ChromeSummaryDao = Depends(get_chrome_summary_dao),
    chrome_logging_dao: ChromeLoggingDao = Depends(get_chrome_logging_dao)
):
    # Lazy import to avoid circular dependency
    from .services.dashboard_service import DashboardService
    return DashboardService(timeline_dao, program_summary_dao, program_logging_dao, chrome_summary_dao, chrome_logging_dao)


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
    system_clock = SystemClock()
    user_facing_clock = UserFacingClock()
    chrome_logging_dao = ChromeLoggingDao(async_session_maker)
    program_logging_dao = ProgramLoggingDao(async_session_maker)

    program_summary_dao = ProgramSummaryDao(
        program_logging_dao, async_session_maker)
    chrome_summary_dao = ChromeSummaryDao(
        chrome_logging_dao, async_session_maker)

    global _arbiter_instance
    if not _arbiter_instance:
        print("Creating new Overlay")
        overlay = Overlay()
        ui_layer = UINotifier(overlay)
        activity_recorder = ActivityRecorder(
            program_summary_dao, chrome_summary_dao)
        print("Creating new ActivityArbiter")
        chrome_service = await get_chrome_service()

        _arbiter_instance = ActivityArbiter(
            user_facing_clock=user_facing_clock
        )

        _arbiter_instance.add_ui_listener(ui_layer.on_state_changed)

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
                                                     async_session_maker)

                                                 )
    return _chrome_service_instance


async def get_video_service(video_dao: VideoDao = Depends(get_video_dao), frame_dao: FrameDao = Depends(get_frame_dao)):
    from .services.services import VideoService
    return VideoService(video_dao, frame_dao)
