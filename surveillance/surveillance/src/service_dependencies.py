# surveillance/src/service_dependencies.py
from surveillance.src.util.clock import SystemClock, UserFacingClock
from fastapi import Depends
from typing import Callable
import asyncio


from surveillance.src.debug.ui_notifier import UINotifier

from surveillance.src.arbiter.activity_arbiter import ActivityArbiter
from surveillance.src.arbiter.activity_recorder import ActivityRecorder
from surveillance.src.arbiter.session_polling import ThreadedEngineContainer


from surveillance.src.services.chrome_service import ChromeService
from surveillance.src.services.tiny_services import KeyboardService, MouseService, TimezoneService
from surveillance.src.facade.facade_singletons import get_keyboard_facade_instance, get_mouse_facade_instance

from surveillance.src.db.database import async_session_maker, regular_session_maker
from surveillance.src.db.dao.queuing.mouse_dao import MouseDao
from surveillance.src.db.dao.queuing.keyboard_dao import KeyboardDao

from surveillance.src.db.dao.queuing.timeline_entry_dao import TimelineEntryDao
from surveillance.src.db.dao.direct.program_summary_dao import ProgramSummaryDao

from surveillance.src.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from surveillance.src.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao


from surveillance.src.db.dao.queuing.video_dao import VideoDao
from surveillance.src.db.dao.direct.frame_dao import FrameDao



# Dependency functions
system_clock = SystemClock()
user_facing_clock = UserFacingClock()

_program_logging_dao = ProgramLoggingDao(
    regular_session_maker)
_chrome_logging_dao = ChromeLoggingDao(
    regular_session_maker)


async def get_keyboard_dao() -> KeyboardDao:
    return KeyboardDao(async_session_maker)


async def get_mouse_dao() -> MouseDao:
    return MouseDao(async_session_maker)


async def get_timeline_dao() -> TimelineEntryDao:
    return TimelineEntryDao(async_session_maker)


async def get_program_summary_dao() -> ProgramSummaryDao:
    # program_logging_dao = ProgramLoggingDao(async_session_maker)
    return ProgramSummaryDao(_program_logging_dao, regular_session_maker, async_session_maker)


async def get_chrome_summary_dao() -> ChromeSummaryDao:
    # chrome_logging_dao = ChromeLoggingDao(async_session_maker)
    return ChromeSummaryDao(_chrome_logging_dao, regular_session_maker, async_session_maker)


async def get_program_logging_dao() -> ProgramLoggingDao:
    return _program_logging_dao


async def get_chrome_logging_dao() -> ChromeLoggingDao:
    return _chrome_logging_dao


async def get_video_dao() -> VideoDao:
    return VideoDao(async_session_maker)


async def get_frame_dao() -> FrameDao:
    return FrameDao(async_session_maker)


# def get_tracker_service() -> TrackerService:
#     keyboard_facade = get_keyboard_facade_instance()
#     mouse_facade = get_mouse_facade_instance()
#     return TrackerService(keyboard_facade, mouse_facade)


async def get_timezone_service() -> TimezoneService:
    from surveillance.src.services.tiny_services import TimezoneService
    return TimezoneService()


async def get_keyboard_service(dao: KeyboardDao = Depends(get_keyboard_dao)) -> KeyboardService:
    from surveillance.src.services.tiny_services import KeyboardService
    return KeyboardService(dao)


async def get_mouse_service(dao: MouseDao = Depends(get_mouse_dao)) -> MouseService:
    # Lazy import to avoid circular dependency
    from surveillance.src.services.tiny_services import MouseService
    return MouseService(dao)


# async def get_program_service() -> ProgramService:
#     # Lazy import to avoid circular dependency
#     from surveillance.src.services.tiny_services import ProgramService
#     return ProgramService(None)  # Under construction


async def get_dashboard_service(
    timeline_dao: TimelineEntryDao = Depends(get_timeline_dao),
    program_summary_dao: ProgramSummaryDao = Depends(get_program_summary_dao),
    program_logging_dao: ProgramLoggingDao = Depends(get_program_logging_dao),
    chrome_summary_dao: ChromeSummaryDao = Depends(get_chrome_summary_dao),
    chrome_logging_dao: ChromeLoggingDao = Depends(get_chrome_logging_dao)
):
    # Lazy import to avoid circular dependency
    from surveillance.src.services.dashboard_service import DashboardService
    return DashboardService(timeline_dao, program_summary_dao, program_logging_dao, chrome_summary_dao, chrome_logging_dao)


# Singleton instance of ActivityArbiter
_arbiter_instance = None
# Singleton instance of ChromeService
_chrome_service_instance = None


async def get_activity_arbiter():
    from surveillance.src.debug.debug_overlay import Overlay
    from surveillance.src.arbiter.activity_arbiter import ActivityArbiter
    from surveillance.src.db.dao.direct.program_summary_dao import ProgramSummaryDao
    from surveillance.src.db.dao.direct.chrome_summary_dao import ChromeSummaryDao

    loop = asyncio.get_event_loop()
    system_clock = SystemClock()
    user_facing_clock = UserFacingClock()
    chrome_logging_dao = ChromeLoggingDao(
        regular_session_maker)
    program_logging_dao = ProgramLoggingDao(
        regular_session_maker)

    program_summary_dao = ProgramSummaryDao(
        program_logging_dao, regular_session_maker, async_session_maker)
    chrome_summary_dao = ChromeSummaryDao(
        chrome_logging_dao, regular_session_maker, async_session_maker)
    
    container = ThreadedEngineContainer(1)

    global _arbiter_instance
    if not _arbiter_instance:
        print("Creating new Overlay")
        overlay = Overlay()
        ui_layer = UINotifier(overlay)
        activity_recorder = ActivityRecorder(user_facing_clock, program_logging_dao, chrome_logging_dao,
                                             program_summary_dao, chrome_summary_dao)
        print("Creating new ActivityArbiter")
        chrome_service = await get_chrome_service()

        _arbiter_instance = ActivityArbiter(
            user_facing_clock=user_facing_clock, threaded_container=container
        )

        _arbiter_instance.add_ui_listener(ui_layer.on_state_changed)
        _arbiter_instance.add_recorder_listener(
            activity_recorder)

        # Create wrapper for async handler
        @chrome_service.event_emitter.on('tab_change')
        def handle_tab_change(tab):
            # Create and schedule the task
            if _arbiter_instance is None:
                raise ValueError("Arbiter instance should be set by now")
            # loop.create_task(_arbiter_instance.set_tab_state(tab))
            _arbiter_instance.set_tab_state(tab)

        print("ActivityArbiter created successfully")
    # else:
        # print(f"Reusing arbiter instance with id: {id(_arbiter_instance)}")

    return _arbiter_instance


async def get_chrome_service(arbiter: ActivityArbiter = Depends(get_activity_arbiter)) -> ChromeService:
    # Lazy import to avoid circular dependency
    from surveillance.src.services.chrome_service import ChromeService
    global _chrome_service_instance  # Singleton because it must preserve internal state
    if _chrome_service_instance is None:
        clock = SystemClock()
        _chrome_service_instance = ChromeService(clock, arbiter)
    return _chrome_service_instance


async def get_video_service(video_dao: VideoDao = Depends(get_video_dao), frame_dao: FrameDao = Depends(get_frame_dao)):
    from surveillance.src.services.tiny_services import VideoService
    return VideoService(video_dao, frame_dao)
