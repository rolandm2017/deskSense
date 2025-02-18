# dashboard_service.py
from datetime import datetime, timedelta, timezone, date

from ..db.dao.timeline_entry_dao import TimelineEntryDao
from ..db.dao.program_summary_dao import ProgramSummaryDao
from ..db.dao.chrome_summary_dao import ChromeSummaryDao
from ..config.definitions import productive_sites_2
from ..console_logger import ConsoleLogger


class DashboardService:
    def __init__(self, timeline_dao: TimelineEntryDao, program_summary_dao: ProgramSummaryDao, chrome_summary_dao: ChromeSummaryDao):
        self.timeline_dao = timeline_dao
        self.program_summary_dao = program_summary_dao
        self.chrome_summary_dao = chrome_summary_dao
        self.logger = ConsoleLogger()

    async def get_timeline(self):
        today = datetime.now()
        all_mouse_events = await self.timeline_dao.read_day_mice(today)
        all_keyboard_events = await self.timeline_dao.read_day_keyboard(today)
        print("all mouse events")
        for v in all_mouse_events[:20]:
            print(v)
        print("all keyboard events")
        for k in all_keyboard_events[:20]:
            print(k)

        return all_mouse_events, all_keyboard_events

      # FIXME Feb 9: I really need to move the Aggregation process to the server
        # FIXME: And possibly ready up Aggregate tables in advance so that
        # FIXME: I don't have to run that compute intensive loop over and over
        # FIXME: a solution could be, each day, the finalized version of the day is computed
        # FIXME: And then the unfinalized day, is sent "live" meaning "what we have recorded so far"
        # FIXME: but the problem is then, how do I determine what is the right Width of stitching
        # FIXME: threshold is the best one? Maybe I should test various ones and see if one is obviously right/wrong

    async def get_current_week_timeline(self):
        # TODO: Logging
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
            self.logger.log_days_retrieval("[get_current_week_timeline]", current_day, len(
                mouse_events) + len(keyboard_events))
            day = {"date": current_day,
                   "mouse_events": mouse_events,
                   "keyboard_events": keyboard_events}
            all_days.append(day)

        return all_days, last_sunday

    async def get_specific_week_timeline(self, week_of):
        if isinstance(week_of, date):
            # Note: The transformation here is a requirement
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
            days_since_sunday = (week_of.weekday() + offset) % days_per_week
            sunday_that_starts_the_week = week_of - \
                timedelta(days=days_since_sunday)

        # TODO: Make this method purely, always, every time, retrieve the precomputed timelines,
        # TODO: as they are by definition tables that already were computed

        # FIXME: The aggregator is messed up. My days are REALLY REALLY long spans. I don't trust the data.

        all_days = []

        # +1 to include today
        v = 0
        for days_after_sunday in range(7):
            self.logger.log_purple(str(v))
            v = v + 1
            current_day = sunday_that_starts_the_week + \
                timedelta(days=days_after_sunday)
            mouse_events = await self.timeline_dao.read_day_mice(current_day)
            keyboard_events = await self.timeline_dao.read_day_keyboard(current_day)
            print(mouse_events, '102ru')
            print(keyboard_events, '103ru')
            self.logger.log_days_retrieval("[get_specific_week_timeline]", current_day, len(
                mouse_events) + len(keyboard_events))
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
