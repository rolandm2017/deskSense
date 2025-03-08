from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
import asyncio
from datetime import timedelta

from ..models import DomainSummaryLog, ProgramSummaryLog
from .base_dao import BaseQueueingDao
from ...util.console_logger import ConsoleLogger


class ProgramLoggingDao(BaseQueueingDao):
    def __init__(self, clock, session_maker: async_sessionmaker, batch_size=100, flush_interval=5):
        """ Exists mostly for debugging. """
        super().__init__(session_maker=session_maker,
                         batch_size=batch_size, flush_interval=flush_interval)
        self.system_clock = clock
        self.session_maker = session_maker

    def create(self, program_name, hours_spent, gathering_date):
        """Log an update to a summary table"""
        log_entry = ProgramSummaryLog(
            program_name=program_name,
            hours_spent=hours_spent,
            gathering_date=gathering_date,
            created_at=self.system_clock.now()
        )
        asyncio.create_task(self.queue_item(log_entry, ProgramSummaryLog))

    async def read_all(self):
        """Fetch all program log entries"""
        async with self.session_maker() as session:
            result = await session.execute(select(ProgramSummaryLog))
            return result.scalars().all()

    async def read_last_24_hrs(self):
        """Fetch all program log entries from the last 24 hours"""
        cutoff_time = self.system_clock.now() - timedelta(hours=24)
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
    def __init__(self, clock, session_maker: async_sessionmaker, batch_size=100, flush_interval=5):
        """ Exists mostly for debugging. """

        super().__init__(session_maker=session_maker,
                         batch_size=batch_size, flush_interval=flush_interval)
        self.system_clock = clock
        self.session_maker = session_maker

    def create(self, domain_name, hours_spent, gathering_date):
        """Log an update to a summary table"""
        log_entry = DomainSummaryLog(
            domain_name=domain_name,
            hours_spent=hours_spent,
            gathering_date=gathering_date,
            created_at=self.system_clock.now()
        )
        asyncio.create_task(self.queue_item(log_entry, DomainSummaryLog))

    async def read_all(self):
        """Fetch all domain log entries"""
        async with self.session_maker() as session:
            result = await session.execute(select(DomainSummaryLog))
            return result.scalars().all()

    async def read_last_24_hrs(self):
        """Fetch all domain log entries from the last 24 hours"""
        cutoff_time = self.system_clock.now() - timedelta(hours=24)
        async with self.session_maker() as session:
            query = select(DomainSummaryLog).where(
                DomainSummaryLog.created_at >= cutoff_time
            ).order_by(DomainSummaryLog.created_at.desc())
            result = await session.execute(query)
            return result.scalars().all()
