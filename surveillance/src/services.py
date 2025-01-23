from fastapi import Depends
from typing import List
from datetime import datetime

from .db.dao.keyboard_dao import KeyboardDao
from .db.dao.program_dao import ProgramDao
from .db.dao.mouse_dao import MouseDao
from .db.dao.chrome_dao import ChromeDao
from .db.dao.timeline_entry_dao import TimelineEntryDao
from .db.dao.daily_summary_dao import DailySummaryDao
from .db.models import TypingSession, Program, MouseMove
from .db.database import get_db, AsyncSession


class KeyboardService:
    def __init__(self, dao: KeyboardDao = Depends()):
        self.dao = dao

    async def get_past_days_events(self) -> List[TypingSession]:
        """
        Returns all keystroke events from the last 24 hours.
        Each keystroke contains a timestamp.
        """
        events = await self.dao.read_past_24h_events()
        return events

    async def get_all_events(self) -> List[TypingSession]:
        """Mostly for debugging"""
        return await self.dao.read_all()


class MouseService:
    def __init__(self, dao: MouseDao = Depends()):
        self.dao = dao

    async def get_past_days_events(self) -> List[MouseMove]:
        """
        Returns all mouse movements that ended in the last 24 hours.
        Each movement contains start_time and end_time.
        """
        events = await self.dao.read_past_24h_events()
        return events

    async def get_all_events(self) -> List[MouseMove]:
        """Mostly for debugging"""
        all = await self.dao.read_all()
        return all


class ProgramService:
    def __init__(self, dao: ProgramDao = Depends()):
        self.dao = dao

    async def get_past_days_events(self) -> List[Program]:
        """
        Returns all program sessions that ended in the last 24 hours.
        Each program session contains window name, start_time, end_time, 
        and productive flag.
        """
        events = await self.dao.read_past_24h_events()
        return events

    async def get_all_events(self) -> List[Program]:
        """Mostly for debugging"""
        print(self.dao, '63vm')
        all = await self.dao.read_all()
        print(all, "in programs.get_all_events")
        return all


class ChromeService:
    def __init__(self, dao: ChromeDao = Depends()):
        self.dao = dao

    async def log_url(self, url_deliverable):
        # TODO: Does it go straight to the db? I guess it does
        print(url_deliverable)


class DashboardService:
    def __init__(self, timeline_dao: TimelineEntryDao, summary_dao: DailySummaryDao):
        self.timeline_dao = timeline_dao
        self.summary_dao = summary_dao

    async def get_timeline(self):
        today = datetime.now()
        all_mouse_events = await self.timeline_dao.read_day_mice(today)
        all_keyboard_events = await self.timeline_dao.read_day_keyboard(today)
        return all_mouse_events, all_keyboard_events

    async def get_program_summary(self):
        today = datetime.now()
        all = await self.summary_dao.read_day(today)
        return all


# Service dependencies
async def get_program_service(db: AsyncSession = Depends(get_db)) -> ProgramService:
    dao = ProgramDao(db)
    return ProgramService(dao)


async def get_mouse_service(db: AsyncSession = Depends(get_db)) -> MouseService:
    dao = MouseDao(db)
    return MouseService(dao)


async def get_keyboard_service(db: AsyncSession = Depends(get_db)) -> KeyboardService:
    dao = KeyboardDao(db)
    return KeyboardService(dao)
