# daily_summary_dao.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker
from asyncio import Queue
from datetime import datetime

from ..models import DailyChromeSummary
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
        # # TODO
        # TODO: Option (1) is to have every tab contain a, uh, a start and end, and thus a duration
        # TODO: another option is to just, like, entry into the db when the tab starts
        # And then the duration is the time between StartTime and uh, the next new tab entry
        # OR startTime and the closure Chrome / the opening of another program

        # ### Check if entry exists for today
        today = datetime.now().date()
        query = select(DailyChromeSummary).where(
            DailyChromeSummary.domain_name == target_domain_name,
            func.date(DailyChromeSummary.gathering_date) == today
        )

        async with self.session_maker() as session:
            result = await session.execute(query)
            existing_entry = result.scalar_one_or_none()

            if existing_entry:
                print("[debug - DAO] adding time ", chrome_session.duration)
                existing_entry.hours_spent += chrome_session.duration
                await session.commit()
            else:
                print("[debug] NEW session: ",
                      chrome_session.domain, chrome_session.duration)
                await self.create(target_domain_name, chrome_session.duration, today)

    async def create(self, target_domain_name, duration_in_hours, today):
        async with self.session_maker() as session:
            new_entry = DailyChromeSummary(
                domain_name=target_domain_name,
                hours_spent=duration_in_hours,
                gathering_date=today
            )
            session.add(new_entry)
            await session.commit()

    async def read_day(self, day: datetime):
        """Read all entries for the given day."""
        query = select(DailyChromeSummary).where(
            func.date(DailyChromeSummary.gathering_date) == day.date()
        )
        async with self.session_maker() as session:

            result = await session.execute(query)
            return result.scalars().all()

    async def read_all(self):
        """Read all entries."""
        async with self.session_maker() as session:
            result = await session.execute(select(DailyChromeSummary))
            return result.scalars().all()

    async def read_row_for_domain(self, target_domain: str):
        """Reads the row for the target program for today."""
        today = datetime.now().date()
        query = select(DailyChromeSummary).where(
            DailyChromeSummary.domain_name == target_domain,
            func.date(DailyChromeSummary.gathering_date) == today
        )
        async with self.session_maker() as session:
            result = await session.execute(query)
            return await result.scalar_one_or_none()

    async def delete(self, id: int):
        """Delete an entry by ID"""
        async with self.session_maker() as session:
            entry = await session.get(DailyChromeSummary, id)
            if entry:
                await session.delete(entry)
                await session.commit()
            return entry
