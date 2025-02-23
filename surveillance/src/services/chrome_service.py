# chrome_service.py
from fastapi import Depends
from typing import List
import asyncio
from datetime import datetime, timedelta, timezone, date
from operator import attrgetter

from ..db.dao.chrome_dao import ChromeDao
from ..db.dao.chrome_summary_dao import ChromeSummaryDao
from ..object.classes import ChromeSessionData
from ..object.pydantic_dto import TabChangeEvent
from ..config.definitions import productive_sites
from ..arbiter.activity_arbiter import ActivityArbiter
from ..util.console_logger import ConsoleLogger


class ChromeService:
    def __init__(self, arbiter: ActivityArbiter, dao: ChromeDao = Depends()):
        print("╠════════╣")
        print("║   **   ║")
        print("║  ****  ║")
        print("║ ****** ║ Starting Chrome Service")
        print("║  ****  ║")
        print("║   **   ║")
        print("╚════════╝")
        self.dao = dao
        self.arbiter = arbiter
        # self.summary_dao = summary_dao
        self.last_entry = None
        self.message_queue = []
        self.ordered_messages = []
        self.ready_queue = []
        self.debounce_timer = None

        # TODO: Get active program. If progrma = chrome, record time. else, do not record.

    # TODO: Log a bunch of real chrome tab submissions, use them in a test

    async def add_to_arrival_queue(self, tab_change_event: TabChangeEvent):
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
        # print("[debug] Starting processing")
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

    def tab_is_transient(self, current, next):
        transience_time_in_ms = 300
        tab_duration = next.startTime - current.startTime
        return tab_duration < timedelta(milliseconds=transience_time_in_ms)

    async def remove_transient_tabs(self):
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
            if self.tab_is_transient(current_event, next_event):
                pass
            else:
                remaining.append(current_event)
        self.ready_queue = remaining
        self.ordered_messages = []

    async def empty_queue_as_sessions(self):
        for event in self.ready_queue:
            await self.log_tab_event(event)
        self.ready_queue = []

    async def log_tab_event(self, url_deliverable: TabChangeEvent):
        """Occurs whenever the user tabs through Chrome tabs.

        A tab comes in and becomes the last entry. Call this the Foo tab.
        A new tab comes in, called Bar, to become the new last entry in place of Foo. 

        The time between Foo's start, and Bar's start, is compared. Bar.start - Foo.start = time_elapsed

        Then, before Bar replaces Foo, Foo has its duration added. Foo is then logged. Cycle repeats.
        """
        # TODO: Write tests for this function
        initialized: ChromeSessionData = ChromeSessionData()
        initialized.domain = url_deliverable.url
        initialized.detail = url_deliverable.tabTitle
        initialized.productive = url_deliverable.url in productive_sites

        if url_deliverable.startTime.tzinfo is not None:
            # Convert start_time to a timezone-naive datetime
            initialized.start_time = url_deliverable.startTime.replace(
                tzinfo=None)
        else:
            initialized.start_time = url_deliverable.startTime

        await self.dao.create(initialized)
        await self.arbiter.set_tab_state(initialized)

        # if self.last_entry:
        #     concluding_session = self.last_entry
        #     #
        #     # Ensure both datetimes are timezone-naive
        #     #
        #     now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        #     start_time_naive = self.last_entry.start_time.replace(tzinfo=None)

        #     if self.elapsed_alt_tab:
        #         duration_of_alt_tab = self.elapsed_alt_tab
        #         self.elapsed_alt_tab = None

        #     duration = now_naive - start_time_naive - duration_of_alt_tab
        #     concluding_session.duration = duration

        # self.last_entry = initialized
        # # print(self.last_entry, '149ru')
        # await self.handle_chrome_ready_for_db(concluding_session)

    # async def handle_close_chrome_session(self, end_time):
    #     current_session_start = self.last_entry.start_time
    #     duration = end_time - current_session_start
    #     self.last_entry.duration = duration

    # def chrome_open_close_handler(self, is_active):
    #     # FIXME:
    #     # FIXME: When Chrome is active, recording time should take place.
    #     # FIXME: When Chrome goes inactive, recording active time should cease.
    #     # FIXME:
    #     # print("[debug] ++ ", str(status))
    #     self.is_active = is_active
    #     if is_active:
    #         self.pause_session_time()
    #     else:
    #         self.activate_session_time()

    # def pause_session_time(self):
    #     """Start a timer"""
    #     self.paused_at = datetime.now()
    #     self.elapsed_alt_tab = None

    # def activate_session_time(self):
    #     """End the timer, subtracting elapsed time from the session"""
    #     self.elapsed_alt_tab = datetime.now() - self.paused_at
    #     self.paused_at = None

    async def shutdown(self):
        """Mostly just logs the final chrome session to the db"""
        pass  # No longer needed in the Arbiter version of the program
        # if self.last_entry:
        #     concluding_session = self.last_entry
        #     #
        #     # Ensure both datetimes are timezone-naive
        #     #
        #     now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        #     start_time_naive = self.last_entry.start_time.replace(tzinfo=None)

        #     duration = now_naive - start_time_naive
        #     concluding_session.duration = duration
        #     await self.handle_chrome_ready_for_db(concluding_session)

    async def handle_chrome_ready_for_db(self, event):
        # TODO: When switch out of Chrome program, stop counting. Confirm.
        await self.summary_dao.create_if_new_else_update(event)
        await self.dao.create(event)

    async def read_last_24_hrs(self):
        return await self.dao.read_past_24h_events()
