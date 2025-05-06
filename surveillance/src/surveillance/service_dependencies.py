# surveillance/src/service_dependencies.py
from surveillance.util.clock import SystemClock, UserFacingClock
from fastapi import Depends
from typing import Callable
import asyncio


from surveillance.debug.ui_notifier import UINotifier

from surveillance.arbiter.activity_arbiter import ActivityArbiter
from surveillance.arbiter.activity_recorder import ActivityRecorder
from surveillance.arbiter.session_polling import ThreadedEngineContainer


from surveillance.services.chrome_service import ChromeService
from surveillance.services.tiny_services import KeyboardService, MouseService, TimezoneService
from surveillance.facade.facade_singletons import get_keyboard_facade_instance, get_mouse_facade_instance

from surveillance.db.database import async_session_maker, regular_session_maker
from surveillance.db.dao.queuing.mouse_dao import MouseDao
from surveillance.db.dao.queuing.keyboard_dao import KeyboardDao

from surveillance.db.dao.queuing.timeline_entry_dao import TimelineEntryDao
from surveillance.db.dao.direct.program_summary_dao import ProgramSummaryDao

from surveillance.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from surveillance.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao


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
    return ProgramSummaryDao(_program_logging_dao, regular_session_maker)


async def get_chrome_summary_dao() -> ChromeSummaryDao:
    return ChromeSummaryDao(_chrome_logging_dao, regular_session_maker)


async def get_program_logging_dao() -> ProgramLoggingDao:
    return _program_logging_dao


async def get_chrome_logging_dao() -> ChromeLoggingDao:
    return _chrome_logging_dao


# def get_tracker_service() -> TrackerService:
#     keyboard_facade = get_keyboard_facade_instance()
#     mouse_facade = get_mouse_facade_instance()
#     return TrackerService(keyboard_facade, mouse_facade)


async def get_timezone_service() -> TimezoneService:
    from surveillance.services.tiny_services import TimezoneService
    return TimezoneService()


async def get_keyboard_service(dao: KeyboardDao = Depends(get_keyboard_dao)) -> KeyboardService:
    from surveillance.services.tiny_services import KeyboardService
    return KeyboardService(dao)


async def get_mouse_service(dao: MouseDao = Depends(get_mouse_dao)) -> MouseService:
    # Lazy import to avoid circular dependency
    from surveillance.services.tiny_services import MouseService
    return MouseService(dao)


# async def get_program_service() -> ProgramService:
#     # Lazy import to avoid circular dependency
#     from surveillance.services.tiny_services import ProgramService
#     return ProgramService(None)  # Under construction


async def get_dashboard_service(
    timeline_dao: TimelineEntryDao = Depends(get_timeline_dao),
    program_summary_dao: ProgramSummaryDao = Depends(get_program_summary_dao),
    program_logging_dao: ProgramLoggingDao = Depends(get_program_logging_dao),
    chrome_summary_dao: ChromeSummaryDao = Depends(get_chrome_summary_dao),
    chrome_logging_dao: ChromeLoggingDao = Depends(get_chrome_logging_dao)
):
    # Lazy import to avoid circular dependency
    from surveillance.services.dashboard_service import DashboardService
    return DashboardService(timeline_dao, program_summary_dao, program_logging_dao, chrome_summary_dao, chrome_logging_dao)


# Singleton instance of ActivityArbiter
_arbiter_instance = None
# Singleton instance of ChromeService
_chrome_service_instance = None


async def get_activity_arbiter():
    from surveillance.debug.debug_overlay import Overlay
    from surveillance.arbiter.activity_arbiter import ActivityArbiter
    from surveillance.db.dao.direct.program_summary_dao import ProgramSummaryDao
    from surveillance.db.dao.direct.chrome_summary_dao import ChromeSummaryDao

    loop = asyncio.get_event_loop()
    system_clock = SystemClock()
    user_facing_clock = UserFacingClock()
    chrome_logging_dao = ChromeLoggingDao(
        regular_session_maker)
    program_logging_dao = ProgramLoggingDao(
        regular_session_maker)

    program_summary_dao = ProgramSummaryDao(
        program_logging_dao, regular_session_maker)
    chrome_summary_dao = ChromeSummaryDao(
        chrome_logging_dao, regular_session_maker)

    container = ThreadedEngineContainer(1)

    global _arbiter_instance
    if not _arbiter_instance:
        print("Creating new Overlay")
        overlay = Overlay()
        ui_layer = UINotifier(overlay)
        activity_recorder = ActivityRecorder(program_logging_dao, chrome_logging_dao,
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
    from surveillance.services.chrome_service import ChromeService
    global _chrome_service_instance  # Singleton because it must preserve internal state
    if _chrome_service_instance is None:
        clock = SystemClock()
        _chrome_service_instance = ChromeService(clock, arbiter)
    return _chrome_service_instance
