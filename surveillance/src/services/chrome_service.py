# chrome_service.py
from fastapi import Depends
from typing import List
from pyee import EventEmitter
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


class TabQueue:
    def __init__(self, log_tab_event):
        self.last_entry = None
        self.message_queue = []
        self.ordered_messages = []
        self.ready_queue = []
        self.debounce_timer = None
        self.log_tab_event = log_tab_event

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
        half_sec = 0.5  # One full sec was too long.
        await asyncio.sleep(half_sec)
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


class ChromeService:
    def __init__(self, clock, arbiter: ActivityArbiter, dao: ChromeDao = Depends()):
        print("╠════════╣")
        print("║ ****** ║ Starting Chrome Service")
        print("╚════════╝")
        self.clock = clock
        self.arbiter = arbiter
        self.dao = dao
        # self.summary_dao = summary_dao

        self.tab_queue = TabQueue(self.log_tab_event)
        self.arbiter = arbiter  # Replace direct arbiter calls

        self.event_emitter = EventEmitter()

        # Set up event handlers
        # self.event_emitter.on('tab_processed', self.log_tab_event)

        self.loop = asyncio.get_event_loop()

        # TODO: Get active program. If progrma = chrome, record time. else, do not record.

    # TODO: Log a bunch of real chrome tab submissions, use them in a test

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

        # Make sure the start time has timezone info
        # ** Whatever the code says, the intent was to
        # ** keep all notions of time consistent. Meaning,
        # ** that the user sent a timestamp from EST
        # ** and the server received it to process it in UTZC
        # ** has absolutely no bearing on the calculated duration
        initialized.start_time = url_deliverable.startTime.astimezone(
            timezone.utc)

        self.handle_session_ready_for_arbiter(initialized)

        if self.last_entry:
            concluding_session = self.last_entry
            # ### Ensure both datetimes are timezone-naive
            now_utc = self.clock.now()
            # Must be utc already since it is set up there
            start_time_naive = self.last_entry.start_time

            if self.elapsed_alt_tab:
                duration_of_alt_tab = self.elapsed_alt_tab
                self.elapsed_alt_tab = None

            duration = now_utc - start_time_naive - duration_of_alt_tab
            concluding_session.duration = duration
            concluding_session.end_time = now_utc

        self.last_entry = initialized

        await self.write_completed_session_to_chrome_dao(concluding_session)

    def write_completed_session_to_chrome_dao(self, session):
        dao_task = self.loop.create_task(self.dao.create(session))

        # Add error callbacks to catch any task failures
        def on_task_done(task):
            try:
                task.result()
            except Exception as e:
                print(f"Task failed with error: {e}")

        dao_task.add_done_callback(on_task_done)

    def handle_session_ready_for_arbiter(self, session):
        self.event_emitter.emit('tab_change', session)

    # FIXME:
    # FIXME: When Chrome is active, recording time should take place.
    # FIXME: When Chrome goes inactive, recording active time should cease.
    # FIXME:

    async def shutdown(self):
        """Mostly just logs the final chrome session to the db"""
        pass  # No longer needed in the Arbiter version of the program
        # Could do stuff like, trigger the Arbiter to shutdown the current state w/o replacement

    async def handle_chrome_ready_for_db(self, event):
        # TODO: When switch out of Chrome program, stop counting. Confirm.
        await self.dao.create(event)

    async def read_last_24_hrs(self):
        return await self.dao.read_past_24h_events()
