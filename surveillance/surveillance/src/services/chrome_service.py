# chrome_service.py
import asyncio
from tracemalloc import start
from urllib.parse import urldefrag
from fastapi import Depends
from typing import List
from pyee import EventEmitter
from datetime import datetime, timedelta, timezone, date
from operator import attrgetter
import copy



from surveillance.src.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from surveillance.src.object.classes import ChromeSession, TabChangeEventWithLtz
from surveillance.src.object.pydantic_dto import UtcDtTabChange
from surveillance.src.config.definitions import productive_sites
from surveillance.src.arbiter.activity_arbiter import ActivityArbiter
from surveillance.src.util.console_logger import ConsoleLogger
from surveillance.src.util.errors import SuspiciousDurationError
from surveillance.src.util.time_wrappers import UserLocalTime


class TabQueue:
    def __init__(self, log_tab_event, debounce_delay=0.5, transience_time_in_ms=300):
        self.last_entry = None
        self.message_queue: list[TabChangeEventWithLtz] = []
        self.ordered_messages: list[TabChangeEventWithLtz] = []
        self.ready_queue: list[TabChangeEventWithLtz] = []
        self.debounce_delay = debounce_delay  # One full sec was too long.
        self.transience_time_in_ms = transience_time_in_ms
        self.debounce_timer = None
        self.log_tab_event = log_tab_event

    def add_to_arrival_queue(self, tab_change_event: TabChangeEventWithLtz):

        self.append_to_queue(tab_change_event)
        MAX_QUEUE_LEN = 40

        if len(self.message_queue) >= MAX_QUEUE_LEN:
            assert self.debounce_timer is not None, "Debounce timer was None when it should exist"
            self.debounce_timer.cancel()
            self.start_processing_msgs()
            return

        if self.debounce_timer:
            self.debounce_timer.cancel()

        self.debounce_timer = asyncio.create_task(self.debounced_process())

    def append_to_queue(self, tab_event):
        """Here to enhance testability"""
        self.message_queue.append(tab_event)

    async def debounced_process(self):
        await asyncio.sleep(self.debounce_delay)
        # print("[debug] Starting processing")
        self.start_processing_msgs()

    def start_processing_msgs(self):
        self.order_message_queue()
        self.remove_transient_tabs()
        self.empty_queue_as_sessions()

    def order_message_queue(self):
        current = self.message_queue
        sorted_events = sorted(current, key=attrgetter('start_time_with_tz'))
        self.ordered_messages = sorted_events
        self.message_queue = []

    def tab_is_transient(self, current: TabChangeEventWithLtz, next: TabChangeEventWithLtz):
        tab_duration = next.start_time_with_tz - current.start_time_with_tz
        return tab_duration < timedelta(milliseconds=self.transience_time_in_ms)

    def remove_transient_tabs(self):
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
                print("Removing transient tab")
                pass
            else:
                remaining.append(current_event)
        self.ready_queue = remaining
        self.ordered_messages = []

    def empty_queue_as_sessions(self):
        for event in self.ready_queue:
            self.log_tab_event(event)
        self.ready_queue = []


class ChromeService:
    def __init__(self, user_facing_clock, arbiter: ActivityArbiter, debounce_delay=0.5):
        print("╠════════╣")
        print("║ ****** ║ Starting Chrome Service")
        print("╚════════╝")
        # FIXME: It can't be a user facing clock b/c it's ... global, server wide.
        self.user_facing_clock = user_facing_clock
        self.arbiter = arbiter
        self.last_entry = None
        self.elapsed_alt_tab = None
        # self.summary_dao = summary_dao

        self.tab_queue = TabQueue(self.log_tab_event, debounce_delay)
        self.arbiter = arbiter  # Replace direct arbiter calls

        self.event_emitter = EventEmitter()

        # Set up event handlers
        # self.event_emitter.on('tab_processed', self.log_tab_event)

        # self.loop = asyncio.get_event_loop()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.logger = ConsoleLogger()


    def log_tab_event(self, url_deliverable: TabChangeEventWithLtz):
        """Occurs whenever the user tabs through Chrome tabs.

        A tab comes in and becomes the last entry. Call this the Foo tab.
        A new tab comes in, called Bar, to become the new last entry in place of Foo. 

        The time between Foo's start, and Bar's start, is compared. Bar.start - Foo.start = time_elapsed

        Then, before Bar replaces Foo, Foo has its duration added. Foo is then logged. Cycle repeats.
        """

        url = url_deliverable.url
        title = url_deliverable.tab_title
        is_productive = url_deliverable.url in productive_sites
        start_time = UserLocalTime(url_deliverable.start_time_with_tz)

        initialized: ChromeSession = ChromeSession(
            url, title, start_time, is_productive)

        # NOTE: In the past, the intent was to keep everything in UTC.
        # Now, the intent is to do everything in the user's LTZ, local time zone.
        # initialized.start_time = url_deliverable.startTime

        self.handle_session_ready_for_arbiter(initialized)

        if self.last_entry:
            # ### Ensure both datetimes are timezone-naive
            # Must be utc already since it is set up there
            if self.last_entry.start_time is None:
                raise ValueError(
                    "last_entry.start_time was None in Chrome Service")
            concluding_start_time: datetime = self.last_entry.start_time.dt

            next_session_start_time = initialized.start_time
            if next_session_start_time is None:
                raise ValueError(
                    "initialized.start_time was None in Chrome Service")

            # duration_of_alt_tab   # used to be a thing
            duration = next_session_start_time - concluding_start_time
            if duration > timedelta(hours=1):
                self.logger.log_red("## ## ## problem in chrome service")
                raise SuspiciousDurationError("duration")
        self.last_entry = initialized

    def handle_session_ready_for_arbiter(self, session):
        session_copy = copy.deepcopy(session)
        # Leads to activityArbiter.set_tab_state
        self.event_emitter.emit('tab_change', session_copy)

    def shutdown(self):
        """Mostly just logs the final chrome session to the db"""
        # Also do stuff like, trigger the Arbiter to shutdown the current state w/o replacement, in other funcs
        self.tab_queue.empty_queue_as_sessions()
