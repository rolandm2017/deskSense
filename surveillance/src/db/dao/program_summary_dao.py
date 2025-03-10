# daily_summary_dao.py
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import async_sessionmaker
from asyncio import Queue
from datetime import datetime, timedelta, timezone
from typing import List

from ..models import DailyProgramSummary
from ...object.classes import ProgramSessionData
from ...util.console_logger import ConsoleLogger
from ...util.debug_logger import write_to_debug_log, write_to_large_usage_log
from ...util.clock import SystemClock


class DatabaseProtectionError(RuntimeError):
    """Custom exception for database protection violations."""
    pass


# @@@@ @@@@ @@@@ @@@@ @@@@
# NOTE: Does not use BaseQueueDao - Because ... <insert reason here when recalled>
# @@@@ @@@@ @@@@ @@@@ @@@@


class ProgramSummaryDao:  # NOTE: Does not use BaseQueueDao
    def __init__(self, logging, session_maker: async_sessionmaker, batch_size=100, flush_interval=5):
        # if not callable(session_maker):
        # raise TypeError("session_maker must be callable")
        self.logging_dao = logging
        self.session_maker = session_maker  # Store the session maker instead of db
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.queue = Queue()
        self.processing = False
        self.logger = ConsoleLogger()

    async def create_if_new_else_update(self, program_session: ProgramSessionData, right_now: datetime):
        """
        This method doesn't use queuing since it needs to check the DB state.

        Note that this method ONLY creates gathering dates that are *today*.

        """
        if program_session.start_time is None or program_session.end_time is None:
            raise ValueError("Start or end time was None")
        target_program_name = program_session.window_title
        # ### Calculate time difference
        usage_duration_in_hours = (
            program_session.end_time - program_session.start_time).total_seconds() / 3600

        # FIXME: maybe the program_session is hanging open while I have the computer sleeping? or something
        # FIXME: Need to define "gathered today" as "between midnight and 11:59 pm on mm-dd"

        # ### Check if entry exists for today
        today = right_now.replace(hour=0, minute=0, second=0,
                                  microsecond=0)  # Still has tz attached

        query = select(DailyProgramSummary).where(
            DailyProgramSummary.program_name == target_program_name,
            DailyProgramSummary.gathering_date >= today,
            DailyProgramSummary.gathering_date < today + timedelta(days=1)
        )

        self.logging_dao.create(target_program_name,
                                usage_duration_in_hours, today, right_now)

        async with self.session_maker() as db_session:
            result = await db_session.execute(query)
            # existing_entry = await result.scalar_one_or_none()  # Adding await here makes the program fail
            # This is how it is properly done, this unawaited version works
            existing_entry = result.scalar_one_or_none()

            if existing_entry:
                # if existing_entry is not None:  # Changed from if existing_entry:
                existing_entry.hours_spent += usage_duration_in_hours
                # if program_session.window_title == "Alt-tab window":
                #     write_to_debug_log(target_program_name, usage_duration_in_hours,
                #                        right_now.strftime("%m-%d %H:%M:%S"))
                # if usage_duration_in_hours > 0.333:
                #     write_to_large_usage_log(program_session,
                #                              usage_duration_in_hours, right_now.strftime("%m-%d %H:%M:%S"))
                await db_session.commit()
            else:
                await self.create(target_program_name, usage_duration_in_hours, today)

    async def create(self, target_program_name, duration_in_hours, when_it_was_gathered):
        async with self.session_maker() as session:
            new_entry = DailyProgramSummary(
                program_name=target_program_name,
                hours_spent=duration_in_hours,
                gathering_date=when_it_was_gathered
            )
            session.add(new_entry)
            await session.commit()

    async def read_past_week(self, right_now: datetime):
        # today = self.system_clock.now()
        # +1 because weekday() counts from Monday=0
        days_since_sunday = right_now.weekday() + 1
        last_sunday = right_now - timedelta(days=days_since_sunday)

        query = select(DailyProgramSummary).where(
            func.date(DailyProgramSummary.gathering_date) >= last_sunday.date()
        )

        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()

    async def read_past_month(self, right_now: datetime):
        """Read all entries from the 1st of the current month through today."""
        # today = self.system_clock.now()
        start_of_month = right_now.replace(day=1)  # First day of current month

        query = select(DailyProgramSummary).where(
            func.date(DailyProgramSummary.gathering_date) >= start_of_month.date()
        )

        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()

    async def read_day(self, day: datetime) -> List[DailyProgramSummary]:
        """Read all entries for the given day."""
        today_start = day.replace(
            hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)
        query = select(DailyProgramSummary).where(
            DailyProgramSummary.gathering_date >= today_start,
            DailyProgramSummary.gathering_date < tomorrow_start
        )
        async with self.session_maker() as session:
            result = await session.execute(query)
            thing = result.scalars().all()
            return thing

    async def read_all(self):
        """Read all entries."""
        async with self.session_maker() as session:
            result = await session.execute(select(DailyProgramSummary))
            return result.scalars().all()

    async def read_row_for_program(self, target_program: str, right_now: datetime):
        """Reads the row for the target program for today."""
        today_start = right_now.replace(
            hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)

        query = select(DailyProgramSummary).where(
            DailyProgramSummary.program_name == target_program,
            DailyProgramSummary.gathering_date >= today_start,
            DailyProgramSummary.gathering_date < tomorrow_start
        )

        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def shutdown(self):
        """Closes the open session without opening a new one"""
        with open("shutdown_proof.txt", "a") as f:
            f.write("shutting down program summary dao")
            f.write("\n")
        pass

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
