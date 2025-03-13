from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import async_sessionmaker
import asyncio
from datetime import timedelta, datetime, date
from typing import List

from ...object.classes import ChromeSessionData, ProgramSessionData

from ..models import DomainSummaryLog, ProgramSummaryLog
from .base_dao import BaseQueueingDao
from ...util.console_logger import ConsoleLogger


class ProgramLoggingDao(BaseQueueingDao):
    def __init__(self, session_maker: async_sessionmaker, batch_size=100, flush_interval=5):
        """ Exists mostly for debugging. """
        super().__init__(session_maker=session_maker,
                         batch_size=batch_size, flush_interval=flush_interval)
        self.session_maker = session_maker

    def create_log(self, session: ProgramSessionData, right_now: datetime):
        """Log an update to a summary table"""
        # ### Calculate time difference
        if session.duration is None:
            raise ValueError("Session duration was None")

        if session.start_time is None or session.end_time is None:
            raise ValueError("Start or end time was None")

        usage_duration_in_hours = (
            session.end_time - session.start_time).total_seconds() / 3600

        log_entry = ProgramSummaryLog(
            program_name=session.window_title,
            hours_spent=usage_duration_in_hours,
            start_time=session.start_time,
            end_time=session.end_time,
            gathering_date=right_now.date(),
            created_at=right_now
        )
        print("[pr] Creating ", log_entry)
        asyncio.create_task(self.queue_item(log_entry, ProgramSummaryLog))

    async def read_day_as_sorted(self, day) -> dict[str, ProgramSummaryLog]:
        start_of_day = day.replace(hour=0, minute=0, second=0,
                                   microsecond=0)  # Still has tz attached
        end_of_day = start_of_day + timedelta(days=1)

        query = select(ProgramSummaryLog).where(
            ProgramSummaryLog.start_time >= start_of_day,
            ProgramSummaryLog.end_time < end_of_day
        ).order_by(ProgramSummaryLog.program_name)

        async with self.session_maker() as session:
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

        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()

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

        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()

    async def read_all(self):
        """Fetch all program log entries"""
        async with self.session_maker() as session:
            result = await session.execute(select(ProgramSummaryLog))
            return result.scalars().all()

    async def read_last_24_hrs(self, right_now: datetime):
        """Fetch all program log entries from the last 24 hours"""
        cutoff_time = right_now - timedelta(hours=24)
        async with self.session_maker() as session:
            query = select(ProgramSummaryLog).where(
                ProgramSummaryLog.created_at >= cutoff_time
            ).order_by(ProgramSummaryLog.created_at.desc())
            result = await session.execute(query)
            return result.scalars().all()

    async def read_suspicious_entries(self):
        """Get entries with durations longer than 20 minutes"""
        suspicious_duration = 0.33333333  # 20 minutes in hours
        async with self.session_maker() as session:
            query = select(ProgramSummaryLog).where(
                ProgramSummaryLog.hours_spent > suspicious_duration
            ).order_by(ProgramSummaryLog.hours_spent.desc())
            result = await session.execute(query)
            return result.scalars().all()

    async def read_suspicious_alt_tab_windows(self):
        """Get alt-tab windows with durations longer than 10 seconds"""
        alt_tab_threshold = 0.0027777  # 10 seconds in hours, or 10/3600
        async with self.session_maker() as session:
            query = select(ProgramSummaryLog).where(
                ProgramSummaryLog.program_name == "Alt-tab window",
                ProgramSummaryLog.hours_spent > alt_tab_threshold
            ).order_by(ProgramSummaryLog.hours_spent.desc())
            result = await session.execute(query)
            return result.scalars().all()


class ChromeLoggingDao(BaseQueueingDao):
    def __init__(self,  session_maker: async_sessionmaker, batch_size=100, flush_interval=5):
        """ Exists mostly for debugging. """

        super().__init__(session_maker=session_maker,
                         batch_size=batch_size, flush_interval=flush_interval)
        self.session_maker = session_maker

    def create_log(self, session: ChromeSessionData, right_now: datetime):
        """Log an update to a summary table"""
        if session.duration is None:
            raise ValueError("Session duration was None")
        if session.start_time is None or session.end_time is None:
            raise ValueError("Start or end time was None")

        usage_duration_in_hours = (
            session.end_time - session.start_time).total_seconds() / 3600

        log_entry = DomainSummaryLog(
            domain_name=session.domain,
            hours_spent=usage_duration_in_hours,
            start_time=session.start_time,
            end_time=session.end_time,
            gathering_date=right_now.date(),
            created_at=right_now
        )
        print("[ch] Creating ", log_entry)
        asyncio.create_task(self.queue_item(log_entry, DomainSummaryLog))

    async def read_day_as_sorted(self, day):
        start_of_day = day.replace(hour=0, minute=0, second=0,
                                   microsecond=0)  # Still has tz attached
        end_of_day = start_of_day + timedelta(days=1)

        query = select(DomainSummaryLog).where(
            DomainSummaryLog.gathering_date >= start_of_day,
            DomainSummaryLog.gathering_date < end_of_day
        ).order_by(DomainSummaryLog.domain_name)

        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()

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

        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()

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

        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()

    async def read_all(self):
        """Fetch all domain log entries"""
        async with self.session_maker() as session:
            result = await session.execute(select(DomainSummaryLog))
            return result.scalars().all()

    async def read_last_24_hrs(self, right_now: datetime):
        """Fetch all domain log entries from the last 24 hours"""
        cutoff_time = right_now - timedelta(hours=24)
        async with self.session_maker() as session:
            query = select(DomainSummaryLog).where(
                DomainSummaryLog.created_at >= cutoff_time
            ).order_by(DomainSummaryLog.created_at.desc())
            result = await session.execute(query)
            return result.scalars().all()
