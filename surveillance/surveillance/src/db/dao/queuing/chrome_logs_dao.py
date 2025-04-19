from sqlalchemy import select, or_
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.asyncio import async_sessionmaker
import asyncio
from datetime import timedelta, datetime, date, timezone
from typing import List

from surveillance.src.object.classes import ChromeSessionData, ProgramSessionData


from surveillance.src.db.models import DomainSummaryLog, ProgramSummaryLog
from surveillance.src.db.dao.base_dao import BaseQueueingDao
from surveillance.src.util.console_logger import ConsoleLogger
from surveillance.src.util.errors import ImpossibleToGetHereError
from surveillance.src.util.dao_wrapper import validate_session, guarantee_start_time
from surveillance.src.util.log_dao_helper import convert_start_end_times_to_hours, convert_duration_to_hours
from surveillance.src.util.time_formatting import convert_to_utc, get_start_of_day
from surveillance.src.util.time_layer import UserLocalTime


#
# #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
# #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
#

class ChromeLoggingDao(BaseQueueingDao):
    """DAO for program activity logging. 
    TIMEZONE HANDLING:
    - All datetimes are stored in UTC by PostgreSQL
    - Methods return UTC timestamps regardless of input timezone
    - Input datetimes should be timezone-aware
    - Date comparisons are performed in UTC"""

    def __init__(self, session_maker: sessionmaker, async_session_maker: async_sessionmaker, batch_size=100, flush_interval=1):
        """ Exists mostly for debugging. """

        super().__init__(async_session_maker=async_session_maker,
                         batch_size=batch_size, flush_interval=flush_interval, dao_name="ChromeLogging")
        self.async_session_maker = async_session_maker
        self.regular_session = session_maker

    def create_log(self, session: ChromeSessionData, right_now: UserLocalTime):
        """
        Log an update to a summary table.

        So the end_time here is like, "when was that addition to the summary ended?"
        """
        if session.duration is None:
            raise ValueError("Session duration was None")
        if session.start_time is None or session.end_time is None:
            raise ValueError("Start or end time was None")
        start_end_time_duration_as_hours = convert_start_end_times_to_hours(
            session)

        duration_property_as_hours = convert_duration_to_hours(session)

        log_entry = DomainSummaryLog(
            domain_name=session.domain,
            hours_spent=start_end_time_duration_as_hours,
            start_time=session.start_time.get_dt_for_db(),
            end_time=session.end_time.get_dt_for_db(),
            duration=duration_property_as_hours,
            gathering_date=right_now.date(),
            created_at=right_now
        )
        with self.regular_session() as db_session:
            db_session.add(log_entry)
            db_session.commit()

    def start_session(self, session: ChromeSessionData):
        """
        A session of using a domain. End_time here is like, "when did the user tab away from the program?"
        """
        if session.start_time is None:
            raise ValueError("Start time was None")
        unknown = None
        base_start_time = convert_to_utc(session.start_time.get_dt_for_db())
        start_of_day = get_start_of_day(session.start_time.get_dt_for_db())
        start_of_day_as_utc = convert_to_utc(start_of_day)
        start_window_end = base_start_time + timedelta(seconds=10)
        log_entry = DomainSummaryLog(
            domain_name=session.domain,
            hours_spent=unknown,
            start_time=base_start_time,
            end_time=start_window_end,
            duration=unknown,
            gathering_date=start_of_day_as_utc,
            created_at=session.start_time.get_dt_for_db()
        )
        with self.regular_session() as db_session:
            db_session.add(log_entry)
            db_session.commit()

    def find_session(self, session: ChromeSessionData):
        if session.start_time is None:
            raise ValueError("Start time was None")
        start_time_as_utc = convert_to_utc(session.start_time.get_dt_for_db())
        query = select(DomainSummaryLog).where(
            DomainSummaryLog.start_time.op('=')(start_time_as_utc)
        )
        with self.regular_session() as db_session:
            result = db_session.execute(query)
            return result.scalar_one_or_none()

    async def read_day_as_sorted(self, day):
        start_of_day = day.replace(hour=0, minute=0, second=0,
                                   microsecond=0)  # Still has tz attached
        end_of_day = start_of_day + timedelta(days=1)

        query = select(DomainSummaryLog).where(
            DomainSummaryLog.gathering_date >= start_of_day,
            DomainSummaryLog.gathering_date < end_of_day
        ).order_by(DomainSummaryLog.domain_name)
        return await self.execute_query(query)

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
        return self.execute_query(query)

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
        return self.execute_query(query)

    def read_all(self):
        """Fetch all domain log entries"""
        query = select(DomainSummaryLog)
        return self.execute_query(query)

    async def read_last_24_hrs(self, right_now: UserLocalTime):
        """Fetch all domain log entries from the last 24 hours"""
        cutoff_time = right_now.dt - timedelta(hours=24)
        query = select(DomainSummaryLog).where(
            DomainSummaryLog.created_at >= cutoff_time
        ).order_by(DomainSummaryLog.created_at.desc())
        return await self.execute_query(query)

    def push_window_ahead_ten_sec(self, session: ChromeSessionData):
        log: DomainSummaryLog = self.find_session(session)
        if not log:
            raise ImpossibleToGetHereError(
                "Start of heartbeat didn't reach the db")
        log.end_time = log.end_time + timedelta(seconds=10)
        with self.regular_session() as db_session:
            db_session.merge(log)
            db_session.commit()

    def finalize_log(self, session: ChromeSessionData):
        """
        Overwrite value from the heartbeat. Expect something to ALWAYS be in the db already at this point.
        Note that if the computer was shutdown, this method is never called, and the rough estimate is kept.
        """
        if session.end_time is None:
            raise ValueError("End time was None")
        log: DomainSummaryLog = self.find_session(session)
        if not log:
            raise ImpossibleToGetHereError(
                "Start of heartbeat didn't reach the db")
        log.end_time = session.end_time.get_dt_for_db()
        with self.regular_session() as db_session:
            db_session.add(log)
            db_session.commit()

    def execute_query(self, query):
        with self.regular_session() as session:
            result = session.execute(query)
            return result.scalars().all()
