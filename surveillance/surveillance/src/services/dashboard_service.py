# dashboard_service.py
from datetime import datetime, timedelta, timezone, date
from typing import List, TypedDict, Dict, Tuple

from surveillance.src.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao


from surveillance.src.db.dao.queuing.timeline_entry_dao import TimelineEntryDao
from surveillance.src.db.dao.direct.program_summary_dao import ProgramSummaryDao
from surveillance.src.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from surveillance.src.db.models import DailyDomainSummary, DailyProgramSummary, ProgramSummaryLog, TimelineEntryObj
from surveillance.src.config.definitions import productive_sites, productive_apps
from surveillance.src.util.console_logger import ConsoleLogger
from surveillance.src.util.clock import UserFacingClock
from surveillance.src.util.time_wrappers import UserLocalTime
from surveillance.src.util.time_formatting import format_for_local_time


class DashboardService:
    def __init__(self, timeline_dao: TimelineEntryDao,
                 program_summary_dao: ProgramSummaryDao,
                 program_logging_dao: ProgramLoggingDao,
                 chrome_summary_dao: ChromeSummaryDao,
                 chrome_logging_dao: ChromeLoggingDao):
        self.timeline_dao = timeline_dao
        self.program_summary_dao = program_summary_dao
        self.program_logging_dao = program_logging_dao
        self.chrome_summary_dao = chrome_summary_dao
        self.chrome_logging_dao = chrome_logging_dao
        self.user_clock = UserFacingClock()
        self.logger = ConsoleLogger()

    async def get_weekly_productivity_overview(self, starting_sunday: UserLocalTime):
        if starting_sunday.weekday() != 6:  # In Python, Sunday is 6
            raise ValueError("start_date must be a Sunday")

        usage_from_days = []

        alt_tab_window_hours = []

        for i in range(7):
            significant_programs = {}  # New dictionary to track programs with >1hr usage

            current_day = starting_sunday + timedelta(days=i)
            date_as_datetime = datetime.combine(
                current_day.dt, datetime.min.time())
            daily_chrome_summaries: List[DailyDomainSummary] = self.chrome_summary_dao.read_day(
                UserLocalTime(date_as_datetime))
            daily_program_summaries: List[DailyProgramSummary] = self.program_summary_dao.read_day(
                UserLocalTime(date_as_datetime))
            productivity = 0
            leisure = 0
            for domain in daily_chrome_summaries:
                if domain.domain_name in productive_sites:
                    productivity = productivity + domain.hours_spent
                else:
                    leisure = leisure + domain.hours_spent

            for program in daily_program_summaries:
                # Make sure Chrome is SKIPPED!
                if program.program_name == "Google Chrome":
                    continue  # Don't double count
                hours_spent: float = float(program.hours_spent)  # type: ignore
                # print(program.program_name, float(
                # f"{program.hours_spent:.4f}"))
                # Track programs with >1hr usage
                if hours_spent > 1:
                    significant_programs[program.program_name] = float(
                        f"{program.hours_spent:.4f}")

                if str(program.program_name) == 'Alt-tab window':
                    alt_tab_window_hours.append(program.hours_spent)
                    continue  # temp - skipping bugged outputs
                if program.program_name in productive_apps:
                    # print("< LOG > adding " + program.program_name)
                    productivity = productivity + hours_spent
                else:
                    leisure = leisure + hours_spent
            day = {"day": date_as_datetime,
                   "productivity": float(f"{productivity:.4f}"), "leisure": float(f"{leisure:.4f}")}

            usage_from_days.append(day
                                   )
        print("alt tab windows: ", alt_tab_window_hours)

        return usage_from_days

    async def get_timeline_for_today(self):
        today = self.user_clock.now()
        all_mouse_events = await self.timeline_dao.read_day_mice(today, self.user_clock)
        all_keyboard_events = await self.timeline_dao.read_day_keyboard(today, self.user_clock)
        return all_mouse_events, all_keyboard_events

    async def get_current_week_timeline(self):
        """Returns whichever days have occurred so far in the present week."""

        today = self.user_clock.now()

        is_sunday = today.weekday() == 6
        if is_sunday:
            # If the week_of is a sunday, start from there.
            sunday_that_starts_the_week = today
            days_since_sunday = 0
        else:
            # If the week_of is not a sunday,
            # go back in time to the most recent sunday,
            # and start from there. This is error handling
            offset = 1
            days_per_week = 7
            days_since_sunday = (today.weekday() + offset) % days_per_week
            sunday_that_starts_the_week = today - \
                timedelta(days=days_since_sunday)

        days_before_today = []

        todays_date = today.date()

        for days_after_sunday in range(7):
            current_day = sunday_that_starts_the_week + \
                timedelta(days=days_after_sunday)
            mouse_events = await self.timeline_dao.read_day_mice(current_day, self.user_clock)
            keyboard_events = await self.timeline_dao.read_day_keyboard(current_day, self.user_clock)

            self.logger.log_days_retrieval("[get_current_week_timeline]", current_day, len(
                mouse_events) + len(keyboard_events))
            day = {"date": current_day,
                   "mouse_events": mouse_events,
                   "keyboard_events": keyboard_events}
            if current_day.date() == todays_date:
                todays_unaggregated_payload = day
            else:
                days_before_today.append(day)

        return days_before_today, todays_unaggregated_payload, sunday_that_starts_the_week

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

        all_days = []

        for days_after_sunday in range(7):
            current_day = sunday_that_starts_the_week + \
                timedelta(days=days_after_sunday)
            mouse_events = await self.timeline_dao.read_day_mice(current_day, self.user_clock)
            keyboard_events = await self.timeline_dao.read_day_keyboard(current_day, self.user_clock)

            # mouse_events_as_local_time = format_for_local_time(mouse_events)
            # keyboard_events_as_local_time = format_for_local_time(
            # keyboard_events)

            self.logger.log_days_retrieval("[get_specific_week_timeline]", current_day, len(
                mouse_events) + len(keyboard_events))
            day = {"date": current_day,
                   "mouse_events": mouse_events,
                   "keyboard_events": keyboard_events}
            all_days.append(day)

        return all_days, sunday_that_starts_the_week

    async def get_current_week_program_usage_timeline(self):
        today = self.user_clock.now()

        is_sunday = today.weekday() == 6
        if is_sunday:
            # If the week_of is a sunday, start from there.
            sunday_that_starts_the_week = today
            days_since_sunday = 0
        else:
            # If the week_of is not a sunday,
            # go back in time to the most recent sunday,
            # and start from there. This is error handling
            offset = 1
            days_per_week = 7
            days_since_sunday = (today.weekday() + offset) % days_per_week
            sunday_that_starts_the_week = today - \
                timedelta(days=days_since_sunday)

        now = self.user_clock.now()
        start_of_today = now.replace(hour=0, minute=0, second=0,
                                     microsecond=0)
        start_of_tomorrow = start_of_today + timedelta(days=1)

        all_days = []

        for days_after_sunday in range(7):
            current_day = sunday_that_starts_the_week + \
                timedelta(days=days_after_sunday)
            is_in_future = current_day > start_of_tomorrow
            if is_in_future:
                continue  # avoid reading future dates from db

            program_usage_timeline: dict[str, ProgramSummaryLog] = await self.program_logging_dao.read_day_as_sorted(current_day)

            self.logger.log_days_retrieval(
                "[get_current_week_program_usage_timeline]", current_day, len(program_usage_timeline))
            day = {"date": current_day,
                   "program_usage_timeline": program_usage_timeline}

            all_days.append(day)

        return all_days, sunday_that_starts_the_week

    async def get_program_usage_timeline_for_week(self, week_of: date) -> Tuple[List[Dict], datetime]:
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

        now = self.user_clock.now()
        start_of_today = now.replace(hour=0, minute=0, second=0,
                                     microsecond=0)
        start_of_tomorrow = start_of_today + timedelta(days=1)

        all_days = []

        for days_after_sunday in range(7):
            current_day = sunday_that_starts_the_week + \
                timedelta(days=days_after_sunday)

            is_in_future = current_day > start_of_tomorrow
            if is_in_future:
                continue  # avoid reading future dates from db

            program_usage_timeline: dict[str, ProgramSummaryLog] = await self.program_logging_dao.read_day_as_sorted(current_day)

            self.logger.log_days_retrieval(
                "[get_program_usage_timeline]", current_day, len(program_usage_timeline))
            day = {"date": current_day,
                   "program_usage_timeline": program_usage_timeline}
            all_days.append(day)

        return all_days, sunday_that_starts_the_week

    async def get_program_summary(self):
        today = self.user_clock.now()
        all = self.program_summary_dao.read_day(today)
        return all

    async def get_chrome_summary(self):
        today = self.user_clock.now()
        all = self.chrome_summary_dao.read_day(today)
        return all

    async def get_program_summary_weekly(self):
        right_now = self.user_clock.now()
        all = self.program_summary_dao.read_past_week(right_now)
        # FIXME: Ensure that it actually gets all days of week; can't test it on Monday
        return all

    async def get_chrome_summary_weekly(self) -> List[DailyDomainSummary]:
        right_now = self.user_clock.now()
        all = self.chrome_summary_dao.read_past_week(right_now)
        # FIXME: Ensure that it actually gets all days of week; can't test it on Monday
        return all

    async def get_previous_week_chrome_summary(self, start_sunday) -> List[DailyDomainSummary]:
        if start_sunday.weekday() != 6:  # In Python, Sunday is 6
            raise ValueError("start_date must be a Sunday")

        usage_from_days = []
        for i in range(7):
            current_day = start_sunday + timedelta(days=i)
            date_as_ult = UserLocalTime(datetime.combine(
                current_day, datetime.min.time()))
            daily_summaries = self.chrome_summary_dao.read_day(
                date_as_ult)

            usage_from_days.extend(daily_summaries)

        return usage_from_days

    async def get_past_month_summaries_programs(self):
        right_now = self.user_clock.now()

        all = await self.program_summary_dao.read_past_month(right_now)
        return all

    async def get_past_month_summaries_chrome(self):
        right_now = self.user_clock.now()

        all = await self.chrome_summary_dao.read_past_month(right_now)
        return all
