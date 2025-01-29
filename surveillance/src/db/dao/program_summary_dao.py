# daily_summary_dao.py
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import async_sessionmaker
from asyncio import Queue
from datetime import datetime

from ..models import DailyProgramSummary
from ...console_logger import ConsoleLogger
from ...object.classes import ProgramSessionData


class DatabaseProtectionError(RuntimeError):
    """Custom exception for database protection violations."""
    pass


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
            # existing_entry = await result.scalar_one_or_none()  # Adding await here makes the program fail
            # This is how it is properly done, this unawaited version works
            existing_entry = result.scalar_one_or_none()

            if existing_entry:
                # if existing_entry is not None:  # Changed from if existing_entry:
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
        print(query, '74ru')
        async with self.session_maker() as session:
            result = await session.execute(query)
            print(result, '77ru')
            thing = result.scalars().all()
            print(thing, '79ru')
            return thing

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
            return result.scalar_one_or_none()

    async def delete(self, id: int):
        """Delete an entry by ID"""
        async with self.session_maker() as session:
            entry = await session.get(DailyProgramSummary, id)
            if entry:
                await session.delete(entry)
                await session.commit()
            return entry

    async def delete_all_rows(self, safety_switch=None) -> int:
        """
        Delete all rows from the DailyProgramSummary table.

        Returns:
            int: The number of rows deleted
        """
        if not safety_switch:
            raise DatabaseProtectionError(
                "Cannot delete all rows without safety switch enabled. "
                "Set safety_switch=True to confirm this action."
            )

        async with self.session_maker() as session:
            result = await session.execute(
                text("DELETE FROM daily_program_summary")
            )
            await session.commit()
            return result.rowcount
