# dashboard_service.py
from typing import List, TypedDict
from datetime import datetime, timedelta, timezone, date

from ..db.dao.timeline_entry_dao import TimelineEntryDao
from ..db.dao.program_summary_dao import ProgramSummaryDao
from ..db.dao.chrome_summary_dao import ChromeSummaryDao
from ..db.models import DailyDomainSummary, DailyProgramSummary
from ..config.definitions import productive_sites, productive_apps
from ..console_logger import ConsoleLogger
from ..object.return_types import DaySummary


class DashboardService:
    def __init__(self, timeline_dao: TimelineEntryDao, program_summary_dao: ProgramSummaryDao, chrome_summary_dao: ChromeSummaryDao):
        self.timeline_dao = timeline_dao
        self.program_summary_dao = program_summary_dao
        self.chrome_summary_dao = chrome_summary_dao
        self.logger = ConsoleLogger()

    async def get_weekly_productivity_overview(self, starting_sunday):
        pass  # Return type has a dayOf field, a productiveHours, a leisureHours

        if starting_sunday.weekday() != 6:  # In Python, Sunday is 6
            raise ValueError("start_date must be a Sunday")

        usage_from_days = []
        # for day in week:
        #     # using the Summary DAO stuff...
        #   # get chrome usage -> categorize as productive | leisure
        #   # get program usage -> categorize
        #       # summarize, store as a day
        #
        # Could store the computed vals too so to avoid recomputing it. Only if it's slow tho, above 100ms
        for i in range(7):
            current_day = starting_sunday + timedelta(days=i)
            date_as_datetime = datetime.combine(
                current_day, datetime.min.time())
            daily_chrome_summaries: List[DailyDomainSummary] = await self.chrome_summary_dao.read_day(date_as_datetime)
            daily_program_summaries: List[DailyProgramSummary] = await self.program_summary_dao.read_day(date_as_datetime)

            productivity = 0
            leisure = 0
            for domain in daily_chrome_summaries:
                if domain in productive_sites:
                    productivity = productivity + domain.hours_spent
                else:
                    leisure = leisure + domain.hours_spent
            for program in daily_program_summaries:
                if program in productive_apps:
                    productivity = productivity + program.hours_spent
                else:
                    leisure = leisure + program.hours_spent

            usage_from_days.append(
                {"day": date_as_datetime, "productivity": productivity, "leisure": leisure})

        return usage_from_days

    async def get_timeline(self):
        today = datetime.now()
        all_mouse_events = await self.timeline_dao.read_day_mice(today)
        all_keyboard_events = await self.timeline_dao.read_day_keyboard(today)
        return all_mouse_events, all_keyboard_events

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
            # print(mouse_events, '102ru')
            # print(keyboard_events, '103ru')
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

    async def get_chrome_summary_weekly(self) -> List[DailyDomainSummary]:
        all = await self.chrome_summary_dao.read_past_week()
        # FIXME: Ensure that it actually gets all days of week; can't test it on Monday
        return all

    async def get_previous_week_chrome_summary(self, start_sunday) -> List[DailyDomainSummary]:
        if start_sunday.weekday() != 6:  # In Python, Sunday is 6
            raise ValueError("start_date must be a Sunday")

        usage_from_days = []
        for i in range(7):
            current_day = start_sunday + timedelta(days=i)
            date_as_datetime = datetime.combine(
                current_day, datetime.min.time())
            daily_summaries = await self.chrome_summary_dao.read_day(
                date_as_datetime)

            usage_from_days.extend(daily_summaries)

        return usage_from_days

    async def get_past_month_summaries_programs(self):
        all = await self.program_summary_dao.read_past_month()
        return all

    async def get_past_month_summaries_chrome(self):
        all = await self.chrome_summary_dao.read_past_month()
        return all
