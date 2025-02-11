# services.py
from fastapi import Depends
from typing import List
import asyncio
from datetime import datetime, timedelta, timezone, date
from operator import attrgetter

from .db.dao.mouse_dao import MouseDao
from .db.dao.keyboard_dao import KeyboardDao
from .db.dao.program_dao import ProgramDao
from .db.dao.timeline_entry_dao import TimelineEntryDao
from .db.dao.program_summary_dao import ProgramSummaryDao
from .db.dao.chrome_dao import ChromeDao
from .db.dao.chrome_summary_dao import ChromeSummaryDao
from .db.dao.video_dao import VideoDao
from .db.dao.frame_dao import FrameDao
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
        print("╠══════════╣")
        print("║    **    ║")
        print("║   ****   ║")
        print("║  ******  ║")
        print("║ ******** ║ Starting Chrome Service")
        print("║  ******  ║")
        print("║   ****   ║")
        print("║    **    ║")
        print("╚══════════╝")
        self.dao = dao
        self.summary_dao = summary_dao
        self.last_entry = None
        self.message_queue = []
        self.ordered_messages = []
        self.ready_queue = []
        self.debounce_timer = None

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

    async def log_tab_event(self, url_deliverable):
        # TODO: Write tests for this function
        initialized: ChromeSessionData = ChromeSessionData()
        initialized.domain = url_deliverable.url
        initialized.detail = url_deliverable.tabTitle
        initialized.productive = url_deliverable.url in productive_sites_2
        # print("FOO")

        if url_deliverable.startTime.tzinfo is not None:
            # Convert start_time to a timezone-naive datetime
            initialized.start_time = url_deliverable.startTime.replace(
                tzinfo=None)
        else:
            initialized.start_time = url_deliverable.startTime

        if self.last_entry:
            concluding_session = self.last_entry
            #
            # Ensure both datetimes are timezone-naive
            #
            now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
            start_time_naive = self.last_entry.start_time.replace(tzinfo=None)

            duration = now_naive - start_time_naive
            concluding_session.duration = duration

        self.last_entry = initialized
        # print(self.last_entry, '149ru')
        await self.handle_chrome_ready_for_db(concluding_session)

    async def handle_close_chrome_session(self, end_time):
        current_session_start = self.last_entry.start_time
        duration = end_time - current_session_start
        self.last_entry.duration = duration

    def chrome_open_close_handler(self, status):
        # FIXME:
        # FIXME: When Chrome is active, recording time should take place.
        # FIXME: When Chrome goes inactive, recording active time should cease.
        # FIXME:
        print("[debug] ++ ", str(status))
        if status:
            self.mark_chrome_active()
        else:
            self.mark_chrome_inactive()

    def mark_chrome_active(self):
        self.is_active = True

    def mark_chrome_inactive(self):
        self.is_active = False

    async def shutdown(self):
        """Mostly just logs the final chrome session to the db"""
        if self.last_entry:
            concluding_session = self.last_entry
            #
            # Ensure both datetimes are timezone-naive
            #
            now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
            start_time_naive = self.last_entry.start_time.replace(tzinfo=None)

            duration = now_naive - start_time_naive
            concluding_session.duration = duration
            await self.handle_chrome_ready_for_db(concluding_session)

    async def handle_chrome_ready_for_db(self, event):
        await self.summary_dao.create_if_new_else_update(event)
        await self.dao.create(event)

    async def read_last_24_hrs(self):
        return await self.dao.read_past_24h_events()


class DashboardService:
    def __init__(self, timeline_dao: TimelineEntryDao, program_summary_dao: ProgramSummaryDao, chrome_summary_dao: ChromeSummaryDao):
        self.timeline_dao = timeline_dao
        self.program_summary_dao = program_summary_dao
        self.chrome_summary_dao = chrome_summary_dao

    async def get_timeline(self):
        today = datetime.now()
        all_mouse_events = await self.timeline_dao.read_day_mice(today)
        all_keyboard_events = await self.timeline_dao.read_day_keyboard(today)
        return all_mouse_events, all_keyboard_events

    async def get_current_week_timeline(self):
        # FIXME Feb 9: I really need to move the Aggregation process to the server
        # FIXME: And possibly ready up Aggregate tables in advance so that
        # FIXME: I don't have to run that compute intensive loop over and over
        # FIXME: a solution could be, each day, the finalized version of the day is computed
        # FIXME: And then the unfinalized day, is sent "live" meaning "what we have recorded so far"
        # FIXME: but the problem is then, how do I determine what is the right Width of stitching
        # FIXME: threshold is the best one? Maybe I should test various ones and see if one is obviously right/wrong
        today = datetime.now()
        # +1 because weekday() counts from Monday=0
        days_since_sunday = today.weekday() + 1
        last_sunday = today - timedelta(days=days_since_sunday)

        # TODO: let the frontend tell the backend how readily to stitch the timeline events together

        all_days = []
        # +1 to include today
        for days_after_sunday in range(days_since_sunday + 1):
            current_day = last_sunday + timedelta(days=days_after_sunday)
            # Or process them directly like your get_timeline() example:
            mouse_events = await self.timeline_dao.read_day_mice(current_day)
            keyboard_events = await self.timeline_dao.read_day_keyboard(current_day)
            day = {"date": current_day,
                   "mouse_events": mouse_events,
                   "keyboard_events": keyboard_events}
            all_days.append(day)

        return all_days, last_sunday

    async def get_specific_week_timeline(self, week_of):
        if isinstance(week_of, date):
            week_of = datetime.combine(week_of, datetime.min.time())
        else:
            raise TypeError("Expected a date object, got " + str(week_of))
        is_sunday = week_of.weekday() == 6
        if is_sunday:
            # If the week_of is a sunday, start from there.
            sunday_that_starts_the_week = week_of
            days_since_sunday = 0
        else:
            # If the week_of is not a sunday,
            # go back in time to the most recent sunday,
            # and start from there. This is error handling
            offset = 1
            days_per_week = 7
            days_since_sunday = week_of.weekday() + offset % days_per_week
            sunday_that_starts_the_week = week_of - \
                timedelta(days=days_since_sunday)

        # TODO: Make this method purely, always, every time, retrieve the precomputed timelines,
        # TODO: as they are by definition tables that already were computed

        all_days = []

        # +1 to include today
        for days_after_sunday in range(days_since_sunday + 1):
            current_day = sunday_that_starts_the_week + \
                timedelta(days=days_after_sunday)
            # Or process them directly like your get_timeline() example:
            print(current_day, type(current_day), '281ru')
            # FIXME: 2025-02-09 281ru
            mouse_events = await self.timeline_dao.read_day_mice(current_day)
            keyboard_events = await self.timeline_dao.read_day_keyboard(current_day)
            day = {"date": current_day,
                   "mouse_events": mouse_events,
                   "keyboard_events": keyboard_events}
            all_days.append(day)

        return all_days, sunday_that_starts_the_week

    async def get_program_summary(self):
        today = datetime.now()
        all = await self.program_summary_dao.read_day(today)
        return all

    async def get_chrome_summary(self):
        today = datetime.now()
        all = await self.chrome_summary_dao.read_day(today)
        return all

    async def get_program_summary_weekly(self):
        all = await self.program_summary_dao.read_past_week()
        # FIXME: Ensure that it actually gets all days of week; can't test it on Monday
        return all

    async def get_chrome_summary_weekly(self):
        all = await self.chrome_summary_dao.read_past_week()
        # FIXME: Ensure that it actually gets all days of week; can't test it on Monday
        return all

    async def get_past_month_summaries_programs(self):
        all = await self.program_summary_dao.read_past_month()
        return all

    async def get_past_month_summaries_chrome(self):
        all = await self.chrome_summary_dao.read_past_month()
        return all


class VideoService:
    def __init__(self, video_dao: VideoDao, frame_dao: FrameDao):
        self.video_dao = video_dao
        self.frame_dao = frame_dao

    async def create_new_video(self, video_create_event):
        self.video_dao.create(video_create_event)

    async def add_frame_to_video(self, add_frame_event):
        self.frame_dao.create(add_frame_event)
