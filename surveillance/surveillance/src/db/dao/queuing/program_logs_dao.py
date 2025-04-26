
from sqlalchemy import select, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import async_sessionmaker
import asyncio
from datetime import timedelta, datetime, date, timezone
from typing import List

from surveillance.src.db.dao.utility_dao_mixin import UtilityDaoMixin
from surveillance.src.db.models import DomainSummaryLog, ProgramSummaryLog
from surveillance.src.db.dao.base_dao import BaseQueueingDao
from surveillance.src.db.dao.utility_dao_mixin import UtilityDaoMixin

from surveillance.src.object.classes import ChromeSession, ProgramSession

from surveillance.src.util.console_logger import ConsoleLogger
from surveillance.src.util.errors import ImpossibleToGetHereError
from surveillance.src.util.dao_wrapper import validate_session, guarantee_start_time
from surveillance.src.util.log_dao_helper import convert_start_end_times_to_hours, convert_duration_to_hours
from surveillance.src.util.time_formatting import convert_to_utc, get_start_of_day
from surveillance.src.util.const import ten_sec_as_pct_of_hour


#
# #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
# #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
#


class ProgramLoggingDao(UtilityDaoMixin):
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

    def start_session(self, session: ProgramSession):
        """
        A session of using a domain. End_time here is like, "when did the user tab away from the program?"
        """
        # self.logger.log_white_multiple(
        #     "INFO: starting session for ", session.window_title)
        if session.start_time is None:
            raise ValueError("Start time was None")
        unknown = None
        base_start_time = convert_to_utc(session.start_time.get_dt_for_db())
        start_of_day = get_start_of_day(session.start_time.get_dt_for_db())
        start_of_day_as_utc = convert_to_utc(start_of_day)
        start_window_end = base_start_time + timedelta(seconds=10)

        log_entry = ProgramSummaryLog(
            exe_path_as_id=session.exe_path,
            process_name=session.process_name,
            program_name=session.window_title,
            # Assumes (10 - n) sec will be deducted later
            hours_spent=ten_sec_as_pct_of_hour,
            start_time=base_start_time,
            end_time=start_window_end,
            duration=unknown,
            gathering_date=start_of_day_as_utc,
            created_at=base_start_time
        )
        # self.do_add_entry(log_entry)
        self.add_new_item(log_entry)

    def find_session(self, session: ProgramSession) -> ProgramSummaryLog | None:
        """Is finding it by time! Looking for the one, specifically, with the arg's time"""
        # the database is storing and returning times in UTC
        if session.start_time is None:
            raise ValueError("Start time was None")
        start_time_as_utc = convert_to_utc(session.start_time.get_dt_for_db())
        query = self.select_where_time_equals(start_time_as_utc)
        return self.execute_and_read_one_or_none(query)

    def select_where_time_equals(self, some_time):
        return select(ProgramSummaryLog).where(
            ProgramSummaryLog.start_time.op('=')(some_time)
        )

    def read_day_as_sorted(self, day) -> dict[str, ProgramSummaryLog]:
        # NOTE: the database is storing and returning times in UTC
        start_of_day = day.replace(hour=0, minute=0, second=0,
                                   microsecond=0)  # Still has tz attached
        end_of_day = start_of_day + timedelta(days=1)

        query = select(ProgramSummaryLog).where(
            ProgramSummaryLog.start_time >= start_of_day,
            ProgramSummaryLog.end_time < end_of_day
        ).order_by(ProgramSummaryLog.program_name)

        logs = self.execute_and_return_all(query)
        # Group the results by program_name
        grouped_logs = {}
        for log in logs:
            if log.program_name not in grouped_logs:
                grouped_logs[log.program_name] = []
            grouped_logs[log.program_name].append(log)

        return grouped_logs
        #   async with self.async_session_maker() as session:
        #     result = await session.execute(query)
        #     logs = result.scalars().all()

        #     # Group the results by program_name
        #     grouped_logs = {}
        #     for log in logs:
        #         if log.program_name not in grouped_logs:
        #             grouped_logs[log.program_name] = []
        #         grouped_logs[log.program_name].append(log)

        #     return grouped_logs

    def find_orphans(self,  latest_shutdown_time, startup_time):
        """
        Finds orphaned sessions that:
        1. Started before shutdown but never ended (end_time is None)
        2. Started before shutdown but ended after next startup (impossible)

        Args:
            latest_shutdown_time: Timestamp when system shut down
            startup_time: Timestamp when system started up again
        """
        query = select(ProgramSummaryLog).where(
            # Started before shutdown
            ProgramSummaryLog.start_time <= latest_shutdown_time,
            # AND (end_time is None OR end_time is after next startup)
            or_(
                ProgramSummaryLog.end_time == None,  # Sessions never closed
                ProgramSummaryLog.end_time >= startup_time  # End time after startup
            )
        ).order_by(ProgramSummaryLog.start_time)
        # the database is storing and returning times in UTC
        return self.execute_and_return_all(query)

    def find_phantoms(self, latest_shutdown_time, startup_time):
        """
        Finds phantom sessions that impossibly started while the system was off.

        Args:
            latest_shutdown_time: Timestamp when system shut down
            startup_time: Timestamp when system started up again
        """
        query = select(ProgramSummaryLog).where(
            # Started after shutdown
            ProgramSummaryLog.start_time > latest_shutdown_time,
            # But before startup
            ProgramSummaryLog.start_time < startup_time
        ).order_by(ProgramSummaryLog.start_time)
        # the database is storing and returning times in UTC
        return self.execute_and_return_all(query)

    def read_all(self):
        """Fetch all program log entries"""
        query = select(ProgramSummaryLog)
        return self.execute_and_return_all(query)

    def read_last_24_hrs(self, right_now: datetime):
        """Fetch all program log entries from the last 24 hours

        NOTE: the database is storing and returning times in UTC
        """
        cutoff_time = right_now - timedelta(hours=24)
        query = select(ProgramSummaryLog).where(
            ProgramSummaryLog.created_at >= cutoff_time
        ).order_by(ProgramSummaryLog.created_at.desc())
        return self.execute_and_return_all(query)

    def read_suspicious_entries(self):
        """Get entries with durations longer than 20 minutes"""
        suspicious_duration = 0.33333333  # 20 minutes in hours
        query = select(ProgramSummaryLog).where(
            ProgramSummaryLog.hours_spent > suspicious_duration
        ).order_by(ProgramSummaryLog.hours_spent.desc())
        return self.execute_and_return_all(query)

    def read_suspicious_alt_tab_windows(self):
        """Get alt-tab windows with durations longer than 10 seconds"""
        alt_tab_threshold = 0.0027777  # 10 seconds in hours, or 10/3600
        query = select(ProgramSummaryLog).where(
            ProgramSummaryLog.program_name == "Alt-tab window",
            ProgramSummaryLog.hours_spent > alt_tab_threshold
        ).order_by(ProgramSummaryLog.hours_spent.desc())
        return self.execute_and_return_all(query)

    def push_window_ahead_ten_sec(self, session: ProgramSession):
        if session is None:
            raise ValueError("Session was None")
        log: ProgramSummaryLog = self.find_session(session)
        if not log:
            raise ImpossibleToGetHereError(
                "Start of heartbeat didn't reach the db")
        log.end_time = log.end_time + timedelta(seconds=10)
        self.update_item(log)

    def finalize_log(self, session: ProgramSession):
        """Overwrite value from the heartbeat. Expect something to ALWAYS be in the db already at this point."""
        if session.end_time is None:
            raise ValueError("End time was None")
        log: ProgramSummaryLog = self.find_session(session)
        if not log:
            raise ImpossibleToGetHereError(
                "Start of heartbeat didn't reach the db")
        log.end_time = session.end_time.get_dt_for_db()
        self.update_item(log)
