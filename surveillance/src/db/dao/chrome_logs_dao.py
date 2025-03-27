from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import async_sessionmaker
import asyncio
from datetime import timedelta, datetime, date, timezone
from typing import List

from ...object.classes import ChromeSessionData, ProgramSessionData

from ..models import DomainSummaryLog, ProgramSummaryLog
from .base_dao import BaseQueueingDao
from ...util.console_logger import ConsoleLogger
from ...util.errors import ImpossibleToGetHereError
from ...util.dao_wrapper import validate_session, guarantee_start_time
from ...util.log_dao_helper import convert_start_end_times_to_hours, convert_duration_to_hours
from ...util.time_formatting import convert_to_utc, get_start_of_day


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
    def __init__(self,  session_maker: async_sessionmaker, batch_size=100, flush_interval=5):
        """ Exists mostly for debugging. """

        super().__init__(session_maker=session_maker,
                         batch_size=batch_size, flush_interval=flush_interval)
        self.session_maker = session_maker

    @validate_session
    def create_log(self, session: ChromeSessionData, right_now: datetime):
        """Log an update to a summary table"""
        start_end_time_duration_as_hours = convert_start_end_times_to_hours(session)

        duration_property_as_hours = convert_duration_to_hours(session)

        log_entry = DomainSummaryLog(
            domain_name=session.domain,
            hours_spent=start_end_time_duration_as_hours,
            start_time=session.start_time,
            end_time=session.end_time,
            duration=duration_property_as_hours,
            gathering_date=right_now.date(),
            created_at=right_now
        )
        asyncio.create_task(self.queue_item(log_entry, DomainSummaryLog))

    @guarantee_start_time
    def start_session(self, session: ChromeSessionData):
        unknown = None
        base_start_time = convert_to_utc(session.start_time)
        start_of_day = get_start_of_day(session.start_time)
        start_of_day_as_utc = convert_to_utc(start_of_day)
        start_window_end = base_start_time + timedelta(seconds=10)
        log_entry = DomainSummaryLog(
            domain_name=session.domain,
            hours_spent=unknown,
            start_time=base_start_time,
            end_time=start_window_end,
            duration=unknown,
            gathering_date=start_of_day_as_utc,
            created_at=session.start_time
        )
        asyncio.create_task(self.queue_item(log_entry, DomainSummaryLog))


    async def find_session(self, session: ChromeSessionData):
        start_time_as_utc = convert_to_utc(session.start_time)
        query = select(DomainSummaryLog).where(
            DomainSummaryLog.start_time == start_time_as_utc
        )
        async with self.session_maker() as db_session:
            result = await db_session.execute(query)
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

    async def find_orphans(self,  latest_shutdown_time, startup_time):
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
        return await self.execute_query(query)

    async def find_phantoms(self, latest_shutdown_time, startup_time):
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
        return await self.execute_query(query)

    async def read_all(self):
        """Fetch all domain log entries"""
        query = select(DomainSummaryLog)
        return await self.execute_query(query)

    async def read_last_24_hrs(self, right_now: datetime):
        """Fetch all domain log entries from the last 24 hours"""
        cutoff_time = right_now - timedelta(hours=24)
        query = select(DomainSummaryLog).where(
                DomainSummaryLog.created_at >= cutoff_time
            ).order_by(DomainSummaryLog.created_at.desc())
        return await self.execute_query(query)

    async def push_window_ahead_ten_sec(self, session: ChromeSessionData):
        log: DomainSummaryLog = await self.find_session(session)
        if not log:
            raise ImpossibleToGetHereError("Start of heartbeat didn't reach the db")
        log.end_time = session.end_time + timedelta(seconds=10)
        async with self.session_maker() as db_session:
            db_session.add(log)
            await db_session.commit()


    async def finalize_log(self, session: ChromeSessionData):
        """Overwrite value from the heartbeat. Expect something to ALWAYS be in the db already at this point."""
        log: DomainSummaryLog = await self.find_session(session)
        if not log:
            raise ImpossibleToGetHereError("Start of heartbeat didn't reach the db")
        log.end_time = session.end_time
        async with self.session_maker() as db_session:
            db_session.add(log)
            await db_session.commit()

    async def execute_query(self, query):
        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()
