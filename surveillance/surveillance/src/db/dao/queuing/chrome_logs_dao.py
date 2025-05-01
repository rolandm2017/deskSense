
import asyncio
from datetime import timedelta, datetime, date, timezone
from typing import List

from sqlalchemy import select, or_
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.asyncio import async_sessionmaker


from surveillance.src.db.dao.utility_dao_mixin import UtilityDaoMixin
from surveillance.src.db.dao.logging_dao_mixin import LoggingDaoMixin

from surveillance.src.db.models import DomainSummaryLog, ProgramSummaryLog
from surveillance.src.db.dao.base_dao import BaseQueueingDao

from surveillance.src.object.classes import ChromeSession, CompletedChromeSession
from surveillance.src.object.dao_util import LogTimeInitializer

from surveillance.src.util.console_logger import ConsoleLogger
from surveillance.src.util.errors import ImpossibleToGetHereError
from surveillance.src.util.dao_wrapper import validate_session, guarantee_start_time
from surveillance.src.util.log_dao_helper import convert_start_end_times_to_hours, convert_duration_to_hours
from surveillance.src.util.time_formatting import convert_to_utc, get_start_of_day_from_datetime, get_start_of_day_from_ult, attach_tz_to_all
from surveillance.src.util.time_wrappers import UserLocalTime
from surveillance.src.util.const import ten_sec_as_pct_of_hour
from surveillance.src.util.log_dao_helper import group_logs_by_name


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
      
    def start_session(self, session: ChromeSession):
        """
        A session of using a domain. End_time here is like, "when did the user tab away from the program?"
        """

        time_initializer = LogTimeInitializer(session.start_time)

        # self.logger.log_white(f"INFO: querying start_of_day: {start_of_day_as_utc}\n\t for {session.get_name()}")

        log_entry = DomainSummaryLog(
            domain_name=session.domain,
            # Assumes (10 - n) sec will be deducted later
            hours_spent=ten_sec_as_pct_of_hour,  # FIXME: all time additions should happen thru KeepAlive
            start_time=time_initializer.base_start_time,
            start_time_local=session.start_time.dt,
            end_time=time_initializer.start_window_end,
            end_time_local=time_initializer.start_window_end.replace(tzinfo=None),
            duration_in_sec=0,
            gathering_date=time_initializer.start_of_day_as_utc,
            gathering_date_local=time_initializer.start_of_day_as_utc.replace(tzinfo=None),
            created_at=time_initializer.base_start_time
        )
        self.add_new_item(log_entry)

    def find_session(self, session: ChromeSession):
        """Is finding it by time! Looking for the one, specifically, with the arg's time"""
        if session.start_time is None:
            raise ValueError("Start time was None")
        start_time_as_utc = convert_to_utc(session.start_time.get_dt_for_db())
        query = self.select_where_time_equals(start_time_as_utc)

        return self.execute_and_read_one_or_none(query)

    def select_where_time_equals(self, some_time):
        return select(DomainSummaryLog).where(
            DomainSummaryLog.start_time.op('=')(some_time)
        )

    def read_day_as_sorted(self, day: UserLocalTime) -> dict[str, DomainSummaryLog]:
        start_of_day = get_start_of_day_from_datetime(day.get_dt_for_db())
        start_of_day = convert_to_utc(start_of_day)
        end_of_day = start_of_day + timedelta(days=1)
        self.logger.log_white(f"INFO: querying start_of_day: {start_of_day}\n\tto end_of_day: {end_of_day}")
        query = select(DomainSummaryLog).where(
            DomainSummaryLog.gathering_date >= start_of_day,
            DomainSummaryLog.gathering_date < end_of_day
        ).order_by(DomainSummaryLog.domain_name)

        query = self.create_read_day_query()

        logs = self.execute_and_return_all(query)

        logs = attach_tz_to_all(logs, day.dt.tzinfo)

        grouped_logs = group_logs_by_name(logs)

        return grouped_logs

    def read_all(self):
        """Fetch all domain log entries"""
        query = select(DomainSummaryLog)
        results = self.execute_and_return_all(query)
        return results  # Developer is trusted to attach tz manually where relevant
        # return self.execute_and_return_all(query)

    def read_last_24_hrs(self, right_now: UserLocalTime):
        """Fetch all domain log entries from the last 24 hours"""
        cutoff_time = right_now.dt - timedelta(hours=24)
        query = select(DomainSummaryLog).where(
            DomainSummaryLog.created_at >= cutoff_time
        ).order_by(DomainSummaryLog.created_at.desc())
        results = self.execute_and_return_all(query)
        return attach_tz_to_all(results, right_now.dt.tzinfo)

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

    def find_orphans(self,  latest_shutdown_time, startup_time):
        """
        Finds orphaned sessions that:
        1. Started before shutdown but never ended (end_time is None)
        2. Started before shutdown but ended after next startup (impossible)

        Args:
            latest_shutdown_time: Timestamp when system shut down
            startup_time: Timestamp when system started up again
        """
        query = select(DomainSummaryLog).where(
            # Started before shutdown
            DomainSummaryLog.start_time <= latest_shutdown_time,
            # AND (end_time is None OR end_time is after next startup)
            or_(
                DomainSummaryLog.end_time == None,  # Sessions never closed
                DomainSummaryLog.end_time >= startup_time  # End time after startup
            )
        ).order_by(DomainSummaryLog.start_time)
        return self.execute_and_return_all(query)

    def find_phantoms(self, latest_shutdown_time, startup_time):
        """
        Finds phantom sessions that impossibly started while the system was off.

        Args:
            latest_shutdown_time: Timestamp when system shut down
            startup_time: Timestamp when system started up again
        """
        query = select(DomainSummaryLog).where(
            # Started after shutdown
            DomainSummaryLog.start_time > latest_shutdown_time,
            # But before startup
            DomainSummaryLog.start_time < startup_time
        ).order_by(DomainSummaryLog.start_time)
        return self.execute_and_return_all(query)