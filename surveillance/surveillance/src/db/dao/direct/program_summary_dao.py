# daily_summary_dao.py
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.sql.selectable import Select
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone, time
from typing import List

from surveillance.src.config.definitions import power_on_off_debug_file

from surveillance.src.db.models import DailyProgramSummary
from surveillance.src.db.dao.utility_dao_mixin import UtilityDaoMixin


from surveillance.src.object.classes import ProgramSession

from surveillance.src.util.dao_wrapper import validate_start_end_and_duration, validate_start_and_end_times
from surveillance.src.util.console_logger import ConsoleLogger
from surveillance.src.util.const import SECONDS_PER_HOUR
from surveillance.src.util.errors import NegativeTimeError, ImpossibleToGetHereError
from surveillance.src.util.debug_util import notice_suspicious_durations, log_if_needed
from surveillance.src.util.time_formatting import get_start_of_day
from surveillance.src.util.time_wrappers import UserLocalTime


class DatabaseProtectionError(RuntimeError):
    """Custom exception for database protection violations."""
    pass


# @@@@ @@@@ @@@@ @@@@ @@@@
# NOTE: Does not use BaseQueueDao - Because ... <insert reason here when recalled>
# @@@@ @@@@ @@@@ @@@@ @@@@


class ProgramSummaryDao(UtilityDaoMixin):  # NOTE: Does not use BaseQueueDao
    def __init__(self, program_logging_dao, reg_session: sessionmaker, async_session_maker: async_sessionmaker):
        # if not callable(session_maker):
        # raise TypeError("session_maker must be callable")
        self.program_logging_dao = program_logging_dao
        self.debug = False
        self.regular_session = reg_session
        self.async_session_maker = async_session_maker
        self.logger = ConsoleLogger()

    def start_session(self, program_session: ProgramSession, right_now):
        target_program_name = program_session.window_title

        starting_window_amt = 10  # sec
        usage_duration_in_hours = starting_window_amt / SECONDS_PER_HOUR

        today_start = get_start_of_day(right_now)

        self._create(program_session.process_name,
                     target_program_name, usage_duration_in_hours, today_start)

    def _create(self, exe_path, target_program_name: str, duration_in_hours: float, when_it_was_gathered: datetime):
        self.throw_if_negative(target_program_name, duration_in_hours)
        new_entry = DailyProgramSummary(
            exe_path=exe_path,
            program_name=target_program_name,
            hours_spent=duration_in_hours,
            gathering_date=when_it_was_gathered
        )
        self.add_new_item(new_entry)

    def find_todays_entry_for_program(self, program_session: ProgramSession):
        """Find by process_name / exe_path"""
        if program_session.start_time is None:
            raise ValueError("start_time was not set")

        start_time = program_session.start_time.dt
        start_of_day = datetime.combine(
            start_time.date(), time.min, tzinfo=start_time.tzinfo)
        end_of_day = datetime.combine(
            start_time.date(), time.max, tzinfo=start_time.tzinfo)

        query = select(DailyProgramSummary).where(
            DailyProgramSummary.exe_path == program_session.process_name,
            DailyProgramSummary.gathering_date >= start_of_day,
            DailyProgramSummary.gathering_date < end_of_day
        )

        return self.exec_and_read_one_or_none(query)

    def read_past_week(self, right_now: UserLocalTime):
        # +1 because weekday() counts from Monday=0
        days_since_sunday = right_now.weekday() + 1
        last_sunday = right_now.dt - timedelta(days=days_since_sunday)

        query = select(DailyProgramSummary).where(
            func.date(DailyProgramSummary.gathering_date) >= last_sunday.date()
        )

        return self.execute_and_return_all(query)

    async def read_past_month(self, right_now: UserLocalTime):
        """Read all entries from the 1st of the current month through today."""
        start_of_month = right_now.replace(day=1)  # First day of current month

        query = select(DailyProgramSummary).where(
            func.date(DailyProgramSummary.gathering_date) >= start_of_month.date()
        )

        return self.execute_and_return_all(query)

    def read_day(self, day: UserLocalTime) -> List[DailyProgramSummary]:
        """Read all entries for the given day."""
        today_start = get_start_of_day(day.dt)
        tomorrow_start = today_start + timedelta(days=1)
        query: Select = select(DailyProgramSummary).where(
            DailyProgramSummary.gathering_date >= today_start,
            DailyProgramSummary.gathering_date < tomorrow_start
        )
        return self.execute_and_return_all(query)

    def read_all(self):
        """Read all entries."""
        query = select(DailyProgramSummary)
        return self.execute_and_return_all(query)

    def read_row_for_program(self, target_program_name: str, right_now: UserLocalTime):
        """Reads the row for the target program for today."""
        today_start = get_start_of_day(right_now.dt)
        tomorrow_start = today_start + timedelta(days=1)

        query = select(DailyProgramSummary).where(
            DailyProgramSummary.program_name == target_program_name,
            DailyProgramSummary.gathering_date >= today_start,
            DailyProgramSummary.gathering_date < tomorrow_start
        )

        return self.exec_and_read_one_or_none(query)

    # Updates section

    def update_hours(self, existing_entry: DailyProgramSummary, usage_duration_in_hours: float):
        """Update hours spent for an existing program entry."""
        with self.regular_session() as session:
            # Reattach the entity to the current session if it's detached
            if existing_entry not in session:
                existing_entry = session.merge(existing_entry)

            # Update the hours
            new_duration = existing_entry.hours_spent + usage_duration_in_hours
            self.throw_if_negative(existing_entry.program_name, new_duration)
            existing_entry.hours_spent = new_duration

            # Commit the changes
            session.commit()

    def push_window_ahead_ten_sec(self, program_session: ProgramSession, right_now: UserLocalTime):
        """
        Finds the given session and adds ten sec to its end_time

        NOTE: This only ever happens after start_session
        """
        if program_session is None:
            raise ValueError("Session should not be None")

        target_program_name = program_session.window_title
        today_start = get_start_of_day(right_now.dt)
        tomorrow_start = today_start + timedelta(days=1)

        query = select(DailyProgramSummary).where(
            DailyProgramSummary.exe_path == program_session.process_name,
            DailyProgramSummary.gathering_date >= today_start,
            DailyProgramSummary.gathering_date < tomorrow_start
        )
        with self.regular_session() as db_session:
            program: DailyProgramSummary = db_session.scalars(query).first()
            # FIXME: Sometimes program is None
            if program:
                program.hours_spent = program.hours_spent + 10 / SECONDS_PER_HOUR
                db_session.commit()
            else:
                raise ImpossibleToGetHereError(
                    "A program should already exist here, but was not found")

    def deduct_remaining_duration(self, session: ProgramSession, duration_in_sec: int, today_start):
        """
        When a session is concluded, it was concluded partway thru the 10 sec window

        9 times out of 10. So we deduct the unfinished duration from its hours_spent.
        """
        if duration_in_sec > 10:
            raise ValueError("Duration was somehow greater than 10")
        target_program_name = session.window_title

        tomorrow_start = today_start + timedelta(days=1)

        time_to_remove = duration_in_sec / SECONDS_PER_HOUR
        self.throw_if_negative(session.window_title, time_to_remove)

        query = select(DailyProgramSummary).where(
            DailyProgramSummary.program_name == target_program_name,
            DailyProgramSummary.gathering_date >= today_start,
            DailyProgramSummary.gathering_date < tomorrow_start
        )
        with self.regular_session() as db_session:
            program: DailyProgramSummary = db_session.scalars(query).first()

            # FIXME: so, hours_spent is not set properly when the
            # new session is created, i think. so when the program
            # comes in here to deduct 5 seconds, there's only 0 seconds existing
            new_duration = program.hours_spent - time_to_remove

            program.hours_spent = new_duration  # Error is here GPT
            db_session.commit()

    def throw_if_negative(self, activity: str, value: int | float):
        if value < 0:
            raise NegativeTimeError(activity, value)

    async def shutdown(self):
        """Closes the open session without opening a new one"""

        pass

    def delete(self, id: int):
        """Delete an entry by ID"""
        with self.regular_session() as session:
            entry = session.get(DailyProgramSummary, id)
            if entry:
                session.delete(entry)
                session.commit()
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

        async with self.async_session_maker() as session:
            result = await session.execute(
                text("DELETE FROM daily_program_summary")
            )
            await session.commit()
            return result.rowcount
