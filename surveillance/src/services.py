from fastapi import Depends
from typing import List
import asyncio
from datetime import datetime, timedelta

from .config.definitions import productive_sites_2, MAX_QUEUE_LENGTH
from .db.dao.keyboard_dao import KeyboardDao
from .db.dao.program_dao import ProgramDao
from .db.dao.mouse_dao import MouseDao
from .db.dao.chrome_dao import ChromeDao
from .db.dao.timeline_entry_dao import TimelineEntryDao
from .db.dao.program_summary_dao import ProgramSummaryDao
from .db.dao.chrome_summary_dao import ChromeSummaryDao
from .object.classes import ChromeSessionData
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
# TODO: Move into a util


def get_start_time(event):
    return datetime.fromisoformat(event["startTime"])


class ChromeService:
    def __init__(self, dao: ChromeDao = Depends(), summary_dao: ChromeSummaryDao = Depends()):
        self.dao = dao
        self.summary_dao = summary_dao
        self.last_entry = None
        self.message_queue = []  # Tab change events may arrive out of order
        self.ordered_messages = []
        self.ready_queue = []

    async def add_to_arrival_queue(self, tab_change_event):
        self.message_queue.append(tab_change_event)

        MAX_QUEUE_LEN = 40

        if len(self.message_queue) >= MAX_QUEUE_LEN:
            self.debounce_timer.cancel()
            await self.start_processing_msgs()
            return

        # Cancel existing timer if there is one
        if self.debounce_timer:
            self.debounce_timer.cancel()

        # Create new timer
        self.debounce_timer = asyncio.create_task(self.debounced_process())

    async def debounced_process(self):
        await asyncio.sleep(1)  # 1 second delay
        await self.start_processing_msgs()

    async def start_processing_msgs(self):
        await self.order_message_queue()
        await self.remove_transient_tabs()
        await self.empty_queue_as_sessions()

    async def order_message_queue(self):
        current = self.message_queue
        sorted_events = sorted(current, key=get_start_time)
        self.ordered_messages = sorted_events
        self.message_queue = []

    async def remove_transient_tabs(self):
        # Assumes events have been ORDERED chronologically
        transience_time_in_ms = 100
        current = self.ordered_messages
        remaining = []
        for i in range(0, len(current)):
            # TODO: Handle edge cases -- final one, just leave it there
            final_msg = len(current) - 1 == i
            if final_msg:
                remaining.append(current[i])
            current = current[i]
            next = current[i + 1]
            tab_duration = next.startTime - current.startTime
            if tab_duration < timedelta(milliseconds=transience_time_in_ms):
                pass
            else:
                remaining.append(current)
        self.ready_queue = remaining
        self.ordered_messages = []

    async def empty_queue_as_sessions(self):
        for event in self.ready_queue:
            self.log_tab_event(event)
        self.ready_queue = []

    async def log_tab_event(self, url_deliverable):

        session: ChromeSessionData = ChromeSessionData()
        session.domain = url_deliverable.url
        session.detail = url_deliverable.tabTitle
        session.productive = url_deliverable.url in productive_sites_2
        session.start_time = url_deliverable.startTime

        if self.last_entry:
            duration = datetime.now() - self.last_entry.start_time
            session.duration = duration
            self.last_entry = session
            await self.handle_chrome_ready_for_db(session)
        else:
            # Must have just started up: No session recorded yet
            session.duration = None
            self.last_entry = session
            await self.handle_chrome_ready_for_db(session)
        # await self.dao.create(url, title, is_productive)

    async def handle_chrome_ready_for_db(self, event):
        self.chrome_summary_dao.create_if_new_else_update(event)
        self.chrome_dao.create(event)

    async def read_last_24_hrs(self):
        return await self.dao.read_past_24h_events()


class DashboardService:
    def __init__(self, timeline_dao: TimelineEntryDao, summary_dao: ProgramSummaryDao):
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
