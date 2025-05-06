# dashboard_service.py
from datetime import datetime, timedelta, timezone, date
from typing import List, TypedDict, Dict, Tuple

from activitytracker.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from activitytracker.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao

from activitytracker.services.tiny_services import TimezoneService
from activitytracker.db.dao.queuing.timeline_entry_dao import TimelineEntryDao
from activitytracker.db.dao.direct.program_summary_dao import ProgramSummaryDao
from activitytracker.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from activitytracker.db.models import (
    DailyDomainSummary,
    DailyProgramSummary,
    ProgramSummaryLog,
    TimelineEntryObj,
)
from activitytracker.config.definitions import productive_sites, productive_apps
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.clock import UserFacingClock
from activitytracker.util.time_wrappers import UserLocalTime
from activitytracker.util.dashboard_svc_mixin import WeekCalculationMixin
from activitytracker.tz_handling.time_formatting import (
    format_for_local_time,
    get_start_of_day_from_datetime,
)


class DashboardService(WeekCalculationMixin):
    def __init__(
        self,
        timeline_dao: TimelineEntryDao,
        program_summary_dao: ProgramSummaryDao,
        program_logging_dao: ProgramLoggingDao,
        chrome_summary_dao: ChromeSummaryDao,
        chrome_logging_dao: ChromeLoggingDao,
    ):
        self.timeline_dao = timeline_dao
        self.program_summary_dao = program_summary_dao
        self.program_logging_dao = program_logging_dao
        self.chrome_summary_dao = chrome_summary_dao
        self.chrome_logging_dao = chrome_logging_dao
        self.user_clock = UserFacingClock()
        self.logger = ConsoleLogger()

        self.timezone_service = TimezoneService()

        self.peripherals = PeripheralsService(
            timeline_dao, self.timezone_service)
        self.programs = ProgramsService(
            program_summary_dao, program_logging_dao, self.timezone_service)

    async def get_weekly_productivity_overview(self, week_of: date):
        if week_of.weekday() != 6:  # In Python, Sunday is 6
            raise ValueError("start_date must be a Sunday")

        starting_sunday: datetime = self.prepare_start_of_week(
            week_of)

        # TODO: Standardize (prepare start of week method)

        usage_from_days = []

        alt_tab_window_hours = []

        for i in range(7):
            # significant_programs = {}  # New dictionary to track programs with >1hr usage

            current_day: datetime = starting_sunday + timedelta(days=i)

            date_with_tz_info: UserLocalTime = self.timezone_service.convert_into_user_timezone_ult(
                current_day)

            daily_chrome_summaries: List[DailyDomainSummary] = (
                self.chrome_summary_dao.read_day(
                    date_with_tz_info)
            )
            daily_program_summaries: List[DailyProgramSummary] = (
                self.program_summary_dao.read_day(
                    date_with_tz_info)
            )
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
                    # TODO: Verify that Chrome doesn't put a session into the Arbiter.
                    continue  # Don't double count
                hours_spent: float = float(program.hours_spent)  # type: ignore

                if str(program.program_name) == "Alt-tab window":
                    alt_tab_window_hours.append(program.hours_spent)
                    continue  # temp - skipping bugged outputs
                if program.program_name in productive_apps:
                    # print("< LOG > adding " + program.program_name)
                    productivity = productivity + hours_spent
                else:
                    leisure = leisure + hours_spent
            day = {
                "day": date_with_tz_info.dt,
                "productivity": float(f"{productivity:.4f}"),
                "leisure": float(f"{leisure:.4f}"),
            }

            usage_from_days.append(day)
        print("alt tab windows: ", alt_tab_window_hours)

        return usage_from_days

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

    async def get_previous_week_chrome_summary(
        self, start_sunday: date
    ) -> List[DailyDomainSummary]:
        if start_sunday.weekday() != 6:  # In Python, Sunday is 6
            raise ValueError("start_date must be a Sunday")
        starting_sunday: datetime = self.prepare_start_of_week(start_sunday)
        usage_from_days = []
        for i in range(7):
            current_day = starting_sunday + timedelta(days=i)

            date_as_ult = self.timezone_service.convert_into_user_timezone_ult(
                current_day)

            daily_summaries = self.chrome_summary_dao.read_day(date_as_ult)

            usage_from_days.extend(daily_summaries)

        return usage_from_days


class ProgramsService(WeekCalculationMixin):
    def __init__(
        self,
        program_summary_dao: ProgramSummaryDao,
        program_logging_dao: ProgramLoggingDao,
        timezone_service: TimezoneService
    ):
        self.program_summary_dao = program_summary_dao
        self.program_logging_dao = program_logging_dao
        self.timezone_service = timezone_service
        self.user_clock = UserFacingClock()
        self.logger = ConsoleLogger()

    async def get_usage_timeline_for_week(
        self, week_of: date
    ) -> Tuple[List[Dict], datetime]:
        """
        week_of: The day according to the user. 

        starting_sunday: The Sunday that is the start of the week being selected.
        """
        starting_sunday: datetime = self.prepare_start_of_week(
            week_of)
        starting_sunday = self.timezone_service.localize_to_user_tz(
            starting_sunday)

        now: UserLocalTime = self.user_clock.now()
        start_of_today: datetime = now.dt.replace(
            hour=0, minute=0, second=0, microsecond=0)
        start_of_tomorrow: datetime = start_of_today + timedelta(days=1)

        all_days = []

        for days_after_sunday in range(7):
            current_day: datetime = starting_sunday + timedelta(
                days=days_after_sunday
            )

            is_in_future = current_day > start_of_tomorrow
            if is_in_future:
                continue  # avoid reading future dates from db

            program_usage_timeline: dict[str, ProgramSummaryLog] = (
                self.program_logging_dao.read_day_as_sorted(
                    UserLocalTime(current_day))
            )
            day = {
                "date": current_day,
                "program_usage_timeline": program_usage_timeline,
            }
            all_days.append(day)

        return all_days, starting_sunday

    async def get_current_week_usage_timeline(self) -> Tuple[List[Dict], datetime]:
        today: UserLocalTime = self.user_clock.now()

        starting_sunday: datetime = self.prepare_start_of_week(today.dt.date())
        starting_sunday = self.timezone_service.localize_to_user_tz(
            starting_sunday)

        now: UserLocalTime = self.user_clock.now()
        start_of_today: UserLocalTime = now.get_start_of_day()
        start_of_tomorrow: UserLocalTime = start_of_today + timedelta(days=1)

        all_days = []

        for days_after_sunday in range(7):
            current_day: datetime = starting_sunday + timedelta(
                days=days_after_sunday
            )
            print(current_day)
            print(start_of_tomorrow)
            is_in_future: bool = current_day > start_of_tomorrow
            if is_in_future:
                continue  # avoid reading future dates from db

            program_usage_timeline: dict[str, ProgramSummaryLog] = self.program_logging_dao.read_day_as_sorted(
                UserLocalTime(current_day))

            # Figure out:
            # - is the problem still happening? are new strange datapoints being made?
            # - where did these ones come from?
            # - how to make pg show them?
            # - how far back does it go? does the problem occur in data from two weeks ago?
            # - if it's still occurring, how to stop it from happening again?
            # - perhaps there can be an auditor dao with some hardcoded values

            self.logger.log_days_retrieval(
                "[get_current_week_program_usage_timeline]",
                current_day,
                len(program_usage_timeline),
            )
            day = {
                "date": current_day,
                "program_usage_timeline": program_usage_timeline,
            }

            all_days.append(day)

        return all_days, starting_sunday


class PeripheralsService(WeekCalculationMixin):
    def __init__(self, timeline_dao: TimelineEntryDao, timezone_service: TimezoneService):
        self.timeline_dao = timeline_dao
        self.timezone_service = timezone_service
        self.user_clock = UserFacingClock()
        self.logger = ConsoleLogger()

    async def get_timeline_for_today(self):
        today = self.user_clock.now()
        all_mouse_events = await self.timeline_dao.read_day_mice(today, self.user_clock)
        all_keyboard_events = await self.timeline_dao.read_day_keyboard(
            today, self.user_clock
        )
        return all_mouse_events, all_keyboard_events

    async def get_current_week_timeline(self) -> Tuple[List[Dict], Dict, datetime]:
        """Returns whichever days have occurred so far in the present week."""

        today = self.user_clock.now()

        starting_sunday: datetime = self.prepare_start_of_week(
            today.date())

        days_before_today = []

        todays_date = today.date()

        for days_after_sunday in range(7):
            current_day = starting_sunday + timedelta(
                days=days_after_sunday
            )
            mouse_events = await self.timeline_dao.read_day_mice(
                UserLocalTime(current_day), self.user_clock
            )
            keyboard_events = await self.timeline_dao.read_day_keyboard(
                UserLocalTime(current_day), self.user_clock
            )

            self.logger.log_days_retrieval(
                "[get_current_week_timeline]",
                current_day,
                len(mouse_events) + len(keyboard_events),
            )
            day = {
                "date": current_day,
                "mouse_events": mouse_events,
                "keyboard_events": keyboard_events,
            }
            if current_day.date() == todays_date:
                todays_unaggregated_payload = day
            else:
                days_before_today.append(day)

        return (
            days_before_today,
            todays_unaggregated_payload,
            starting_sunday,
        )

    async def get_specific_week_timeline(self, week_of: date) -> Tuple[List[Dict], datetime]:

        starting_sunday: datetime = self.prepare_start_of_week(
            week_of)

        all_days = []

        for days_after_sunday in range(7):
            current_day: datetime = starting_sunday + timedelta(
                days=days_after_sunday
            )

            current_day_ult = self.timezone_service.convert_into_user_timezone_ult(
                current_day)

            mouse_events = await self.timeline_dao.read_day_mice(
                current_day_ult, self.user_clock
            )
            keyboard_events = await self.timeline_dao.read_day_keyboard(
                current_day_ult, self.user_clock
            )

            self.logger.log_days_retrieval(
                "[get_specific_week_timeline]",
                current_day,
                len(mouse_events) + len(keyboard_events),
            )
            day = {
                "date": current_day,
                "mouse_events": mouse_events,
                "keyboard_events": keyboard_events,
            }
            all_days.append(day)

        return all_days, starting_sunday
