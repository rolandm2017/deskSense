
from sqlalchemy import select, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import async_sessionmaker
import asyncio
from datetime import timedelta, datetime, date, timezone
from typing import List

from ....object.classes import ChromeSessionData, ProgramSessionData

from ...models import DomainSummaryLog, ProgramSummaryLog
from ..base_dao import BaseQueueingDao
from ....util.console_logger import ConsoleLogger
from ....util.errors import ImpossibleToGetHereError
from ....util.dao_wrapper import validate_session, guarantee_start_time
from ....util.log_dao_helper import convert_start_end_times_to_hours, convert_duration_to_hours
from ....util.time_formatting import convert_to_utc, get_start_of_day

#
# #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #  
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
# #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #  
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
#


class ProgramLoggingDao(BaseQueueingDao):
    """DAO for program activity logging. 
    TIMEZONE HANDLING:
    - All datetimes are stored in UTC by PostgreSQL
    - Methods return UTC timestamps regardless of input timezone
    - Input datetimes should be timezone-aware
    - Date comparisons are performed in UTC"""
    def __init__(self, session_maker: sessionmaker, async_session_maker: async_sessionmaker, batch_size=100, flush_interval=1, dao_name="ProgramLogging"):
        """ Exists mostly for debugging. """
        super().__init__(async_session_maker=async_session_maker,
                         batch_size=batch_size, flush_interval=flush_interval, dao_name=dao_name)
        self.regular_session = session_maker
        self.async_session_maker = async_session_maker

    @validate_session
    def create_log(self, session: ProgramSessionData, right_now: datetime):
        """
        Log an update to a summary table.
        
        So the end_time here is like, "when was that addition to the summary ended?"
        """
        # ### Calculate time difference
        start_end_time_duration_as_hours = convert_start_end_times_to_hours(session)

        duration_property_as_hours = convert_duration_to_hours(session)

        # FIXME: do not need hours_spent AND duration?

        log_entry = ProgramSummaryLog(
            program_name=session.window_title,
            hours_spent=start_end_time_duration_as_hours,
            start_time=session.start_time,
            end_time=session.end_time,
            duration=duration_property_as_hours,
            gathering_date=right_now.date(),
            created_at=right_now
        )
        # print("[pr] Creating ", log_entry)
        with self.regular_session() as db_session:
            db_session.add(log_entry)
            db_session.commit()


    @guarantee_start_time
    def start_session(self, session: ProgramSessionData):
        """
        A session of using a domain. End_time here is like, "when did the user tab away from the program?"
        """
        print("[debug] starting session for ", session.window_title)
        unknown = None
        base_start_time = convert_to_utc(session.start_time)
        start_of_day = get_start_of_day(session.start_time)
        start_of_day_as_utc = convert_to_utc(start_of_day)
        start_window_end = base_start_time + timedelta(seconds=10)
        log_entry = ProgramSummaryLog(
            program_name=session.window_title,
            hours_spent=unknown,
            start_time=base_start_time,
            end_time=start_window_end,
            duration=unknown,
            gathering_date=start_of_day_as_utc,
            created_at=base_start_time
        )
        with self.regular_session() as db_session:
            db_session.add(log_entry)
            db_session.commit()


    def find_session(self, session: ProgramSessionData):
        # the database is storing and returning times in UTC
        start_time_as_utc = convert_to_utc(session.start_time)
        query = select(ProgramSummaryLog).where(
            ProgramSummaryLog.start_time == start_time_as_utc
        )
        with self.regular_session() as db_session:
            result = db_session.execute(query)
            return result.scalar_one_or_none()


    async def read_day_as_sorted(self, day) -> dict[str, ProgramSummaryLog]:
        # NOTE: the database is storing and returning times in UTC
        start_of_day = day.replace(hour=0, minute=0, second=0,
                                   microsecond=0)  # Still has tz attached
        end_of_day = start_of_day + timedelta(days=1)

        query = select(ProgramSummaryLog).where(
            ProgramSummaryLog.start_time >= start_of_day,
            ProgramSummaryLog.end_time < end_of_day
        ).order_by(ProgramSummaryLog.program_name)

        async with self.async_session_maker() as session:
            result = await session.execute(query)
            logs = result.scalars().all()

            # Group the results by program_name
            grouped_logs = {}
            for log in logs:
                if log.program_name not in grouped_logs:
                    grouped_logs[log.program_name] = []
                grouped_logs[log.program_name].append(log)

            return grouped_logs

    async def find_orphans(self,  latest_shutdown_time, startup_time):
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
        return await self.execute_query(query)  # the database is storing and returning times in UTC
        # async with self.async_session_maker() as session:
            # result = await session.execute(query)
            # return result.scalars().all()

    async def find_phantoms(self, latest_shutdown_time, startup_time):
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
        return await self.execute_query(query)  # the database is storing and returning times in UTC

    async def read_all(self):
        """Fetch all program log entries"""
        query = select(ProgramSummaryLog)
        return await self.execute_query(query)

    async def read_last_24_hrs(self, right_now: datetime):
        """Fetch all program log entries from the last 24 hours
        
        NOTE: the database is storing and returning times in UTC
        """
        cutoff_time = right_now - timedelta(hours=24)
        query = select(ProgramSummaryLog).where(
            ProgramSummaryLog.created_at >= cutoff_time
        ).order_by(ProgramSummaryLog.created_at.desc())
        return await self.execute_query(query)

    async def read_suspicious_entries(self):
        """Get entries with durations longer than 20 minutes"""
        suspicious_duration = 0.33333333  # 20 minutes in hours
        query = select(ProgramSummaryLog).where(
                ProgramSummaryLog.hours_spent > suspicious_duration
            ).order_by(ProgramSummaryLog.hours_spent.desc())
        return await self.execute_query(query)
        
    async def read_suspicious_alt_tab_windows(self):
        """Get alt-tab windows with durations longer than 10 seconds"""
        alt_tab_threshold = 0.0027777  # 10 seconds in hours, or 10/3600
        query = select(ProgramSummaryLog).where(
                ProgramSummaryLog.program_name == "Alt-tab window",
                ProgramSummaryLog.hours_spent > alt_tab_threshold
            ).order_by(ProgramSummaryLog.hours_spent.desc())
        return await self.execute_query(query)
        
    async def push_window_ahead_ten_sec(self, session: ProgramSessionData):
        log: ProgramSummaryLog = await self.find_session(session)
        if not log:
            raise ImpossibleToGetHereError("Start of heartbeat didn't reach the db")
        log.end_time = session.end_time + timedelta(seconds=10)
        async with self.async_session_maker() as db_session:
            db_session.add(log)
            await db_session.commit()

    def finalize_log(self, session: ProgramSessionData):
        """Overwrite value from the heartbeat. Expect something to ALWAYS be in the db already at this point."""
        log: ProgramSummaryLog = self.find_session(session)
        if not log:
            raise ImpossibleToGetHereError("Start of heartbeat didn't reach the db")
        log.end_time = session.end_time
        with self.regular_session() as db_session:
            db_session.add(log)
            db_session.commit()

    async def execute_query(self, query):
        async with self.async_session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()
