# daily_summary_dao.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker

import traceback
from datetime import datetime, timedelta, time
from typing import List

from surveillance.src.config.definitions import keep_alive_cycle_length, window_push_length
from surveillance.src.db.dao.utility_dao_mixin import UtilityDaoMixin
from surveillance.src.db.dao.summary_dao_mixin import SummaryDaoMixin
from surveillance.src.db.models import DailyDomainSummary

from surveillance.surveillance.src.tz_handling.dao_objects import FindTodaysEntryInitializer
from surveillance.src.object.classes import ChromeSession

from surveillance.src.util.console_logger import ConsoleLogger
from surveillance.src.util.errors import NegativeTimeError, ImpossibleToGetHereError
from surveillance.src.util.const import SECONDS_PER_HOUR
from surveillance.surveillance.src.tz_handling.time_formatting import get_start_of_day_from_datetime, attach_tz_to_all, attach_tz_to_obj, get_start_of_day_from_ult
from surveillance.src.util.time_wrappers import UserLocalTime


class ChromeSummaryDao(SummaryDaoMixin, UtilityDaoMixin):
    def __init__(self,  chrome_logging_dao, regular_session: sessionmaker):
        self.chrome_logging_dao = chrome_logging_dao
        self.debug = False
        self.regular_session = regular_session
        self.logger = ConsoleLogger()
        self.model = DailyDomainSummary

    def start_session(self, chrome_session: ChromeSession):
        target_domain_name = chrome_session.domain

        self._create(target_domain_name, chrome_session.start_time.dt)

    def _create(self, target_domain_name, start_time_dt: datetime):
        # self.logger.log_white(
        #     f"[info] creating for {target_domain_name} with duration {duration_in_hours * SECONDS_PER_HOUR}")
        today = get_start_of_day_from_datetime(
            start_time_dt)  # Still has tz attached

        new_entry = DailyDomainSummary(
            domain_name=target_domain_name,
            hours_spent=0,
            gathering_date=today,
            gathering_date_local=start_time_dt.replace(tzinfo=None)
        )
        self.add_new_item(new_entry)

    def find_todays_entry_for_domain(self, chrome_session: ChromeSession) -> DailyDomainSummary | None:
        """Find by domain name"""
        initializer = FindTodaysEntryInitializer(chrome_session.start_time)

        query = self.create_find_all_from_day_query(
            chrome_session.domain, initializer.start_of_day_with_tz, initializer.end_of_day_with_tz)

        return self._execute_read_with_restored_tz(query, chrome_session.start_time)

    def create_find_all_from_day_query(self, domain_name, start_of_day, end_of_day):
        # Use LTZ
        return select(DailyDomainSummary).where(
            DailyDomainSummary.domain_name == domain_name,
            DailyDomainSummary.gathering_date >= start_of_day,
            DailyDomainSummary.gathering_date < end_of_day
        )

    def read_past_week(self, right_now: UserLocalTime):
        return self.do_read_past_week(right_now)

    def read_day(self, day: UserLocalTime) -> List[DailyDomainSummary]:
        """Read all entries for the given day."""
        return self.do_read_day(day)

    def read_all(self) -> List[DailyDomainSummary]:
        """Read all entries."""
        query = select(DailyDomainSummary)
        # Developer handles it manually
        return self.execute_and_return_all(query)

    def push_window_ahead_ten_sec(self, chrome_session: ChromeSession):
        """Finds the given session and adds ten sec to its end_time

        NOTE: This only ever happens after start_session
        """
        today_start = get_start_of_day_from_datetime(
            chrome_session.start_time.dt)
        query = self.select_where_time_equals_for_session(
            today_start, chrome_session.domain)
        self.execute_window_push(
            query, chrome_session.domain, chrome_session.start_time.dt)

    def select_where_time_equals_for_session(self, some_time, target_domain):
        return select(DailyDomainSummary).where(
            DailyDomainSummary.gathering_date.op('=')(some_time),
            DailyDomainSummary.domain_name == target_domain
        )

    def add_used_time(self, session: ChromeSession, duration_in_sec: int):
        """
        When a session is concluded, it was concluded partway thru the 10 sec window

        9 times out of 10. So we add  the used  duration from its hours_spent.
        """
        self.add_partial_window(session, duration_in_sec,
                                DailyDomainSummary.domain_name == session.domain)

    def shutdown(self):
        """Closes the open session without opening a new one"""
        pass
