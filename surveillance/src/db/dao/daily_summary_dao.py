# daily_summary_dao.py
# TODO
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from asyncio import Queue
import asyncio
from datetime import datetime, timedelta

from ..models import DailyProgramSummary
from ...console_logger import ConsoleLogger
from ...object.classes import SessionData

# @@@@ @@@@ @@@@ @@@@ @@@@
# NOTE: Does not use BaseQueueDao
# @@@@ @@@@ @@@@ @@@@ @@@@


class DailySummaryDao:  # NOTE: Does not use BaseQueueDao
    def __init__(self, db: AsyncSession, batch_size=100, flush_interval=5):
        super().__init__(db, batch_size, flush_interval)
        self.logger = ConsoleLogger()

    async def create_if_new_else_update(self, session: SessionData):
        """This method doesn't use queuing since it needs to check the DB state"""
        target_program_name = session['window']
        # ### Calculate time difference
        start_time = datetime.fromisoformat(session['start_time'])
        end_time = datetime.fromisoformat(session['end_time'])
        # Convert to hours
        usage_duration_in_hours = (
            end_time - start_time).total_seconds() / 3600

        # ### Check if entry exists for today
        today = datetime.now().date()
        query = select(DailyProgramSummary).where(
            DailyProgramSummary.programName == target_program_name,
            func.date(DailyProgramSummary.date) == today
        )
        result = await self.db.execute(query)
        existing_entry = result.scalar_one_or_none()

        if existing_entry:
            # Update existing entry
            existing_entry.hoursSpent += usage_duration_in_hours
            await self.db.commit()
        else:
            self.create(target_program_name, usage_duration_in_hours, today)

    async def create(self, target_program_name, duration_in_hours, today):
        # Create new entry
        new_entry = DailyProgramSummary(
            programName=target_program_name,
            hoursSpent=duration_in_hours,
            date=today
        )
        self.db.add(new_entry)
        await self.db.commit()

    async def read_day(self, day: datetime):
        """Read all entries for the given day."""
        query = select(DailyProgramSummary).where(
            func.date(DailyProgramSummary.date) == day.date()
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def read_all(self):
        """Read all entries."""
        result = await self.db.execute(select(DailyProgramSummary))
        return result.scalars().all()

    async def read_row_for_program(self, target_program: str):
        """Reads the row for the target program for today."""
        today = datetime.now().date()
        query = select(DailyProgramSummary).where(
            DailyProgramSummary.programName == target_program,
            func.date(DailyProgramSummary.date) == today
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def delete(self, id: int):
        """Delete an entry by ID"""
        entry = await self.db.get(DailyProgramSummary, id)
        if entry:
            await self.db.delete(entry)
            await self.db.commit()
        return entry
