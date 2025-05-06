
import asyncio
from datetime import timedelta, datetime, date, timezone
from typing import List

from sqlalchemy import select, or_
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.asyncio import async_sessionmaker


from activitytracker.db.dao.utility_dao_mixin import UtilityDaoMixin
from activitytracker.db.dao.logging_dao_mixin import LoggingDaoMixin

from activitytracker.db.models import DomainSummaryLog, ProgramSummaryLog

from activitytracker.object.classes import ChromeSession, CompletedChromeSession
from activitytracker.tz_handling.dao_objects import LogTimeConverter

from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.errors import ImpossibleToGetHereError
from activitytracker.util.log_dao_helper import convert_start_end_times_to_hours, convert_duration_to_hours
from activitytracker.tz_handling.time_formatting import convert_to_utc, get_start_of_day_from_datetime, get_start_of_day_from_ult, attach_tz_to_all
from activitytracker.util.time_wrappers import UserLocalTime
from activitytracker.util.const import ten_sec_as_pct_of_hour
from activitytracker.util.log_dao_helper import group_logs_by_name


#
# #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
# #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
#

class ChromeLoggingDao(LoggingDaoMixin, UtilityDaoMixin):
    """DAO for program activity logging. 
    TIMEZONE HANDLING:
    - All datetimes are stored in UTC by PostgreSQL
    - Methods return UTC timestamps regardless of input timezone
    - Input datetimes should be timezone-aware
    - Date comparisons are performed in UTC"""

    def __init__(self, session_maker: sessionmaker):
        """ Exists mostly for debugging. """

        self.regular_session = session_maker  # Do not delete. UtilityDao still uses it
        self.logger = ConsoleLogger()
        self.model = DomainSummaryLog

    def start_session(self, session: ChromeSession):
        """
        A session of using a domain. End_time here is like, "when did the user tab away from the program?"
        """

        initializer = LogTimeConverter(session.start_time)

        log_entry = DomainSummaryLog(
            domain_name=session.domain,
            # Assumes (10 - n) sec will be deducted later
            # FIXME: all time additions should happen thru KeepAlive
            hours_spent=ten_sec_as_pct_of_hour,
            start_time=initializer.base_start_time_as_utc,
            start_time_local=session.start_time.dt,
            end_time=initializer.base_start_window_end,
            end_time_local=initializer.base_start_window_end.replace(
                tzinfo=None),
            duration_in_sec=0,
            gathering_date=initializer.start_of_day_as_utc,
            gathering_date_local=initializer.start_of_day_as_utc.replace(
                tzinfo=None),
            created_at=initializer.base_start_time_as_utc
        )
        self.add_new_item(log_entry)

    def find_session(self, session: ChromeSession):
        """Is finding it by time! Looking for the one, specifically, with the arg's time"""
        if session.start_time is None:
            raise ValueError("Start time was None")
        start_time_as_utc = convert_to_utc(
            session.start_time.get_dt_for_db())
        query = self.select_where_time_equals(start_time_as_utc)

        return self.execute_and_read_one_or_none(query)

    def select_where_time_equals(self, some_time):
        return select(DomainSummaryLog).where(
            DomainSummaryLog.start_time.op('=')(some_time)
        )

    def read_day_as_sorted(self, day: UserLocalTime) -> dict[str, DomainSummaryLog]:
        # NOTE: the database is storing and returning times in UTC
        return self._read_day_as_sorted(day, DomainSummaryLog, DomainSummaryLog.domain_name)

    def read_all(self) -> List[DomainSummaryLog]:
        """Fetch all domain log entries"""
        query = select(DomainSummaryLog)
        results = self.execute_and_return_all(query)
        return results  # Developer is trusted to attach tz manually where relevant
        # return self.execute_and_return_all(query)

    def read_last_24_hrs(self, right_now: UserLocalTime):
        """Fetch all domain log entries from the last 24 hours"""
        return self.do_read_last_24_hrs(right_now)

    def push_window_ahead_ten_sec(self, session: ChromeSession):
        log: DomainSummaryLog = self.find_session(session)
        if not log:
            raise ImpossibleToGetHereError(
                "Start of pulse didn't reach the db")
        log.end_time = log.end_time + timedelta(seconds=10)
        self.update_item(log)

    def finalize_log(self, session: CompletedChromeSession):
        """
        Overwrite value from the pulse. Expect something to ALWAYS be in the db already at this point.
        Note that if the computer was shutdown, this method is never called, and the rough estimate is kept.
        """
        log: DomainSummaryLog = self.find_session(session)
        if not log:
            raise ImpossibleToGetHereError(
                "Start of pulse didn't reach the db")
        self.attach_final_values_and_update(session, log)
