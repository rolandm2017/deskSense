# chrome_service.py
from tracemalloc import start
from urllib.parse import urldefrag
from fastapi import Depends
from typing import List
from pyee import EventEmitter
import asyncio
from datetime import datetime, timedelta, timezone, date
from operator import attrgetter


from ..config.definitions import power_on_off_debug_file

from ..db.dao.chrome_dao import ChromeDao
from ..db.dao.chrome_summary_dao import ChromeSummaryDao
from ..object.classes import ChromeSessionData
from ..object.pydantic_dto import TabChangeEvent
from ..config.definitions import productive_sites
from ..arbiter.activity_arbiter import ActivityArbiter
from ..util.console_logger import ConsoleLogger
from ..util.errors import SuspiciousDurationError


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
            assert self.debounce_timer is not None, "Debounce timer was None when it should exist"
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
    def __init__(self, user_facing_clock, arbiter: ActivityArbiter, dao: ChromeDao = Depends()):
        print("╠════════╣")
        print("║ ****** ║ Starting Chrome Service")
        print("╚════════╝")
        # FIXME: It can't be a user facing clock b/c it's ... global, server wide.
        self.user_facing_clock = user_facing_clock
        self.arbiter = arbiter
        self.dao = dao
        self.last_entry = None
        self.elapsed_alt_tab = None
        # self.summary_dao = summary_dao

        self.tab_queue = TabQueue(self.log_tab_event)
        self.arbiter = arbiter  # Replace direct arbiter calls

        self.event_emitter = EventEmitter()

        # Set up event handlers
        # self.event_emitter.on('tab_processed', self.log_tab_event)

        self.loop = asyncio.get_event_loop()
        self.logger = ConsoleLogger()

    # TODO: Log a bunch of real chrome tab submissions, use them in a test

    def log_tab_event(self, url_deliverable: TabChangeEvent):
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

        # temp = url_deliverable.startTime
        # print("DEBUG: ",  temp)
        # print(
        #     f"[DEBUG] tzinfo: {temp.tzinfo}")

        # NOTE: In the past, the intent was to keep everything in UTC.
        # Now, the intent is to do everything in the user's LTZ, local time zone.
        initialized.start_time = url_deliverable.startTime

        self.handle_session_ready_for_arbiter(initialized)

        if self.last_entry:
            concluding_session = self.last_entry
            # ### Ensure both datetimes are timezone-naive
            # Must be utc already since it is set up there
            concluding_start_time: datetime = self.last_entry.start_time  # type: ignore

            next_session_start_time = initialized.start_time

            # FIXME: duration is impossibly long, like hours. it might be a TZ problem

            # duration_of_alt_tab   # used to be a thing
            duration = next_session_start_time - concluding_start_time
            if duration > timedelta(hours=1):
                self.logger.log_red("## ## ##")
                self.logger.log_red("## ## ## problem in chrome service")
                self.logger.log_red("## ## ##")
                raise SuspiciousDurationError("duration")
            concluding_session.duration = duration
            concluding_session.end_time = next_session_start_time
        self.last_entry = initialized
        self.write_completed_session_to_chrome_dao(concluding_session)

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
        print(session, type(session), "185ru")
        self.event_emitter.emit('tab_change', session)

    # FIXME: When Chrome is active, recording time should take place.
    # FIXME: When Chrome goes inactive, recording active time should cease.

    async def shutdown(self):
        """Mostly just logs the final chrome session to the db"""
        # Also do stuff like, trigger the Arbiter to shutdown the current state w/o replacement, in other funcs
        await self.tab_queue.empty_queue_as_sessions()
        with open(power_on_off_debug_file, "a") as f:
            f.write("Shutdown Chrome Service\n")

    async def handle_chrome_ready_for_db(self, event):
        await self.dao.create(event)

    async def read_last_24_hrs(self):
        right_now = self.user_facing_clock.now()
        return await self.dao.read_past_24h_events(right_now)
