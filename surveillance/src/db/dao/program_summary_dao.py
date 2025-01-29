# daily_summary_dao.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker
from asyncio import Queue
from datetime import datetime

from ..models import DailyProgramSummary
from ...console_logger import ConsoleLogger
from ...object.classes import ProgramSessionData

# @@@@ @@@@ @@@@ @@@@ @@@@
# NOTE: Does not use BaseQueueDao
# @@@@ @@@@ @@@@ @@@@ @@@@


class ProgramSummaryDao:  # NOTE: Does not use BaseQueueDao
    def __init__(self, session_maker: async_sessionmaker, batch_size=100, flush_interval=5):
        # if not callable(session_maker):
        # raise TypeError("session_maker must be callable")
        self.session_maker = session_maker  # Store the session maker instead of db
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.queue = Queue()
        self.processing = False
        self.logger = ConsoleLogger()

    async def create_if_new_else_update(self, program_session: ProgramSessionData):
        """This method doesn't use queuing since it needs to check the DB state"""
        target_program_name = program_session.window_title
        # ### Calculate time difference
        usage_duration_in_hours = (
            program_session.end_time - program_session.start_time).total_seconds() / 3600

        # ### Check if entry exists for today
        today = datetime.now().date()
        query = select(DailyProgramSummary).where(
            DailyProgramSummary.program_name == target_program_name,
            func.date(DailyProgramSummary.gathering_date) == today
        )

        async with self.session_maker() as db_session:
            result = await db_session.execute(query)
            print(result, '41ru')
            # existing_entry = await result.scalar_one_or_none()  # Adding await here makes the program fail
            # This is how it is properly done, this unawaited version works
            existing_entry = result.scalar_one_or_none()

            print(f"Type of existing_entry: {type(existing_entry)}")
            print(f"Dir of existing_entry: {dir(existing_entry)}")

            if existing_entry:
                # if existing_entry is not None:  # Changed from if existing_entry:
                print(f"Program name: {existing_entry.program_name}")
                existing_entry.hours_spent += usage_duration_in_hours
                await db_session.commit()
            else:
                await self.create(target_program_name, usage_duration_in_hours, today)

    async def create(self, target_program_name, duration_in_hours, today):
        async with self.session_maker() as session:
            new_entry = DailyProgramSummary(
                program_name=target_program_name,
                hours_spent=duration_in_hours,
                gathering_date=today
            )
            session.add(new_entry)
            await session.commit()

    async def read_day(self, day: datetime):
        """Read all entries for the given day."""
        query = select(DailyProgramSummary).where(
            func.date(DailyProgramSummary.gathering_date) == day.date()
        )
        async with self.session_maker() as session:

            result = await session.execute(query)
            return result.scalars().all()

    async def read_all(self):
        """Read all entries."""
        async with self.session_maker() as session:
            result = await session.execute(select(DailyProgramSummary))
            return result.scalars().all()

    async def read_row_for_program(self, target_program: str):
        """Reads the row for the target program for today."""
        today = datetime.now().date()
        query = select(DailyProgramSummary).where(
            DailyProgramSummary.program_name == target_program,
            func.date(DailyProgramSummary.gathering_date) == today
        )
        async with self.session_maker() as session:
            result = await session.execute(query)
            # return await result.scalar_one_or_none()
            # return result.scalar_one_or_none()

    async def delete(self, id: int):
        """Delete an entry by ID"""
        async with self.session_maker() as session:
            entry = await session.get(DailyProgramSummary, id)
            if entry:
                await session.delete(entry)
                await session.commit()
            return entry
