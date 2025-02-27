# daily_summary_dao.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker
from asyncio import Queue
from datetime import datetime, timedelta

from ..models import DailyDomainSummary
from ...console_logger import ConsoleLogger
from ...object.classes import ChromeSessionData

# @@@@ @@@@ @@@@ @@@@ @@@@
# NOTE: Does not use BaseQueueDao
# @@@@ @@@@ @@@@ @@@@ @@@@


class ChromeSummaryDao:  # NOTE: Does not use BaseQueueDao
    def __init__(self, session_maker: async_sessionmaker, batch_size=100, flush_interval=5):
        self.session_maker = session_maker  # Store the session maker instead of db
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.queue = Queue()
        self.processing = False
        self.logger = ConsoleLogger()

    async def create_if_new_else_update(self, chrome_session: ChromeSessionData):
        """This method doesn't use queuing since it needs to check the DB state"""
        target_domain_name = chrome_session.domain
        # ### Calculate time difference

        usage_duration_in_hours = chrome_session.duration.total_seconds() / 3600

        # ### Check if entry exists for today
        today = datetime.now().date()  # FIXME: could be getting 0 hrs today b/c of the
        query = select(DailyDomainSummary).where(
            DailyDomainSummary.domain_name == target_domain_name,
            func.date(DailyDomainSummary.gathering_date) == today
        )

        async with self.session_maker() as session:
            result = await session.execute(query)
            existing_entry = result.scalar_one_or_none()

            if existing_entry:
                self.logger.log_white_multiple("[chrome summary dao] adding time ",
                                               chrome_session.duration, " to ", existing_entry.domain_name)
                existing_entry.hours_spent += usage_duration_in_hours
                await session.commit()
            else:
                print("[debug] NEW session: ",
                      chrome_session.domain, usage_duration_in_hours)
                await self.create(target_domain_name, usage_duration_in_hours, today)

    async def create(self, target_domain_name, duration_in_hours, today):
        async with self.session_maker() as session:
            new_entry = DailyDomainSummary(
                domain_name=target_domain_name,
                hours_spent=duration_in_hours,
                gathering_date=today
            )
            session.add(new_entry)
            await session.commit()

    async def read_past_week(self):
        today = datetime.now()
        # +1 because weekday() counts from Monday=0
        days_since_sunday = today.weekday() + 1
        last_sunday = today - timedelta(days=days_since_sunday)
        query = select(DailyDomainSummary).where(
            func.date(DailyDomainSummary.gathering_date) >= last_sunday.date()
        )

        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()

    async def read_past_month(self):
        """Read all entries from the 1st of the current month through today."""
        today = datetime.now()
        start_of_month = today.replace(day=1)  # First day of current month

        query = select(DailyDomainSummary).where(
            func.date(DailyDomainSummary.gathering_date) >= start_of_month.date()
        )

        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()

    async def read_day(self, day: datetime):
        """Read all entries for the given day."""

        query = select(DailyDomainSummary).where(
            func.date(DailyDomainSummary.gathering_date) == day.date()
        )
        async with self.session_maker() as session:

            result = await session.execute(query)
            return result.scalars().all()

    async def read_all(self):
        """Read all entries."""
        async with self.session_maker() as session:
            result = await session.execute(select(DailyDomainSummary))
            return result.scalars().all()

    async def read_row_for_domain(self, target_domain: str):
        """Reads the row for the target program for today."""
        today = datetime.now().date()
        query = select(DailyDomainSummary).where(
            DailyDomainSummary.domain_name == target_domain,
            func.date(DailyDomainSummary.gathering_date) == today
        )
        async with self.session_maker() as session:
            result = await session.execute(query)
            return await result.scalar_one_or_none()

    async def delete(self, id: int):
        """Delete an entry by ID"""
        async with self.session_maker() as session:
            entry = await session.get(DailyDomainSummary, id)
            if entry:
                await session.delete(entry)
                await session.commit()
            return entry
