# services.py
from fastapi import Depends
from typing import List
import asyncio
from datetime import datetime, timedelta
from operator import attrgetter

from .db.dao.mouse_dao import MouseDao
from .db.dao.keyboard_dao import KeyboardDao
from .db.dao.program_dao import ProgramDao
from .db.dao.timeline_entry_dao import TimelineEntryDao
from .db.dao.program_summary_dao import ProgramSummaryDao
from .db.dao.chrome_dao import ChromeDao
from .db.dao.chrome_summary_dao import ChromeSummaryDao
from .object.classes import ChromeSessionData
from .db.models import TypingSession, Program, MouseMove
from .object.pydantic_dto import TabChangeEvent
from .config.definitions import productive_sites_2


class KeyboardService:
    def __init__(self, dao: KeyboardDao = Depends()):
        self.dao = dao

    async def get_past_days_events(self) -> List[TypingSession]:
        events = await self.dao.read_past_24h_events()
        return events

    async def get_all_events(self) -> List[TypingSession]:
        return await self.dao.read_all()


class MouseService:
    def __init__(self, dao: MouseDao = Depends()):
        self.dao = dao

    async def get_past_days_events(self) -> List[MouseMove]:
        events = await self.dao.read_past_24h_events()
        return events

    async def get_all_events(self) -> List[MouseMove]:
        return await self.dao.read_all()


class ProgramService:
    def __init__(self, dao: ProgramDao = Depends()):
        self.dao = dao

    async def get_past_days_events(self) -> List[Program]:
        events = await self.dao.read_past_24h_events()
        return events

    async def get_all_events(self) -> List[Program]:
        return await self.dao.read_all()


class ChromeService:
    def __init__(self, dao: ChromeDao = Depends(), summary_dao: ChromeSummaryDao = Depends()):
        self.dao = dao
        self.summary_dao = summary_dao
        self.last_entry = None
        self.message_queue = []
        self.ordered_messages = []
        self.ready_queue = []
        self.debounce_timer = None

    # TODO: Log a bunch of real chrome tab submissions, use them in a test

    async def add_to_arrival_queue(self, tab_change_event: TabChangeEvent):
        print("[DEBUG] adding ", tab_change_event, '70ru')
        self.message_queue.append(tab_change_event)

        MAX_QUEUE_LEN = 40

        if len(self.message_queue) >= MAX_QUEUE_LEN:
            self.debounce_timer.cancel()
            await self.start_processing_msgs()
            return

        if self.debounce_timer:
            self.debounce_timer.cancel()

        self.debounce_timer = asyncio.create_task(self.debounced_process())

    async def debounced_process(self):
        one_second = 1  # TODO: Try 0.5 sec also
        await asyncio.sleep(one_second)
        print("[debug] Starting processing")
        await self.start_processing_msgs()

    async def start_processing_msgs(self):
        await self.order_message_queue()
        await self.remove_transient_tabs()
        await self.empty_queue_as_sessions()

    async def order_message_queue(self):
        current = self.message_queue
        sorted_events = sorted(current, key=attrgetter('startTime'))
        self.ordered_messages = sorted_events
        self.message_queue = []

    async def remove_transient_tabs(self):
        transience_time_in_ms = 100
        current_queue = self.ordered_messages
        if len(current_queue) == 0:
            return
        remaining = []
        for i in range(0, len(current_queue)):
            final_msg = len(current_queue) - 1 == i
            if final_msg:
                remaining.append(current_queue[i])
                break
            current_event = current_queue[i]
            next_event = current_queue[i + 1]
            tab_duration = next_event.startTime - current_event.startTime
            if tab_duration < timedelta(milliseconds=transience_time_in_ms):
                pass
            else:
                remaining.append(current_event)
        self.ready_queue = remaining
        self.ordered_messages = []

    async def empty_queue_as_sessions(self):
        for event in self.ready_queue:
            await self.log_tab_event(event)
        self.ready_queue = []

    async def log_tab_event(self, url_deliverable):
        session: ChromeSessionData = ChromeSessionData()
        session.domain = url_deliverable.url
        session.detail = url_deliverable.tabTitle
        session.productive = url_deliverable.url in productive_sites_2
        session.start_time = url_deliverable.startTime

        if url_deliverable.startTime.tzinfo is not None:
            # Convert start_time to a timezone-naive datetime
            session.start_time = url_deliverable.startTime.replace(tzinfo=None)
        else:
            session.start_time = url_deliverable.startTime

        if self.last_entry:
            duration = datetime.now() - self.last_entry.start_time
            session.duration = duration
        else:
            session.duration = 0

        self.last_entry = session
        await self.handle_chrome_ready_for_db(session)

    async def handle_chrome_ready_for_db(self, event):
        await self.summary_dao.create_if_new_else_update(event)
        await self.dao.create(event)

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
