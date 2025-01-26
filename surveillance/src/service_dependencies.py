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


async def get_keyboard_service(dao: KeyboardDao = Depends(get_keyboard_dao)) -> Callable:
    from .services import KeyboardService
    return KeyboardService(dao)

# async def get_keyboard_service(dao: KeyboardDao = Depends(KeyboardDao)) -> Callable:
    # Lazy import to avoid circular dependency
    # from .services import KeyboardService
    # return KeyboardService(dao)


async def get_mouse_service(dao: MouseDao = Depends(get_mouse_dao)) -> Callable:
    from .services import MouseService  # Lazy import to avoid circular dependency
    return MouseService(dao)


async def get_program_service(dao: ProgramDao = Depends(get_program_dao)) -> Callable:
    from .services import ProgramService  # Lazy import to avoid circular dependency
    return ProgramService(dao)


async def get_dashboard_service(
    timeline_dao: TimelineEntryDao = Depends(get_timeline_dao),
    summary_dao: ProgramSummaryDao = Depends(get_program_summary_dao)
) -> Callable:
    # Lazy import to avoid circular dependency
    from .services import DashboardService
    return DashboardService(timeline_dao, summary_dao)


async def get_chrome_service(
    dao: ChromeDao = Depends(get_chrome_dao),
    summary_dao: ChromeSummaryDao = Depends(get_chrome_summary_dao)
) -> Callable:
    from .services import ChromeService  # Lazy import to avoid circular dependency
    return ChromeService(dao, summary_dao)
