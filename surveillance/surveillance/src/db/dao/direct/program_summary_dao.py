# daily_summary_dao.py
from sqlalchemy import select, func, text
from sqlalchemy.sql.selectable import Select
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, time
from typing import List

from surveillance.src.config.definitions import keep_alive_cycle_length, window_push_length

from surveillance.src.db.models import DailyProgramSummary
from surveillance.src.db.dao.utility_dao_mixin import UtilityDaoMixin
from surveillance.src.db.dao.summary_dao_mixin import SummaryDaoMixin


from surveillance.surveillance.src.tz_handling.dao_objects import FindTodaysEntryConverter
from surveillance.src.object.classes import ProgramSession

from surveillance.src.util.console_logger import ConsoleLogger
from surveillance.src.util.const import SECONDS_PER_HOUR
from surveillance.src.util.errors import NegativeTimeError, ImpossibleToGetHereError
from surveillance.surveillance.src.tz_handling.time_formatting import get_start_of_day_from_datetime, attach_tz_to_all, attach_tz_to_obj, get_start_of_day_from_ult
from surveillance.src.util.time_wrappers import UserLocalTime


class ProgramSummaryDao(SummaryDaoMixin, UtilityDaoMixin):
    def __init__(self, program_logging_dao, reg_session: sessionmaker):
        # if not callable(session_maker):
        # raise TypeError("session_maker must be callable")
        self.program_logging_dao = program_logging_dao
        self.debug = False
        self.regular_session = reg_session
        self.logger = ConsoleLogger()
        self.model = DailyProgramSummary

    def start_session(self, program_session: ProgramSession):
        """Creating the initial session for the summary"""
        self._create(program_session, program_session.start_time.dt)

    def _create(self, session: ProgramSession, start_time: datetime):
        # self.logger.log_white("[debug] creating session: " + session.exe_path
        today_start = get_start_of_day_from_datetime(start_time)

        new_entry = DailyProgramSummary(
            exe_path_as_id=session.exe_path,
            program_name=session.window_title,
            process_name=session.process_name,
            hours_spent=0,
            gathering_date=today_start,
            gathering_date_local=today_start.replace(tzinfo=None)
        )
        self.add_new_item(new_entry)

    def find_todays_entry_for_program(self, program_session: ProgramSession) -> DailyProgramSummary | None:
        """Find by exe_path"""
        initializer = FindTodaysEntryConverter(program_session.start_time)

        query = self.create_find_all_from_day_query(
            program_session.exe_path, initializer.start_of_day_with_tz, initializer.end_of_day_with_tz)

        return self._execute_read_with_restored_tz(query, program_session.start_time)

    def create_find_all_from_day_query(self, exe_path, start_of_day, end_of_day):
        # Use LTZ
        return select(DailyProgramSummary).where(
            DailyProgramSummary.exe_path_as_id == exe_path,
            DailyProgramSummary.gathering_date >= start_of_day,
            DailyProgramSummary.gathering_date < end_of_day
        )

    def read_past_week(self, right_now: UserLocalTime):
        # +1 because weekday() counts from Monday=0
        return self.do_read_past_week(right_now)

    def read_day(self, day: UserLocalTime) -> List[DailyProgramSummary]:
        """Read all entries for the given day."""
        return self.do_read_day(day)

    def read_all(self) -> List[DailyProgramSummary]:
        """Read all entries."""
        query = select(DailyProgramSummary)
        return self.execute_and_return_all(query)

    # Updates section

    def push_window_ahead_ten_sec(self, program_session: ProgramSession):
        """
        Finds the given session and adds ten sec to its end_time

        NOTE: This only ever happens after start_session
        """
        if program_session is None:
            raise ValueError("Session should not be None")

        today_start = get_start_of_day_from_datetime(
            program_session.start_time.dt)
        query = self.select_where_time_equals_for_session(
            today_start, program_session.exe_path)

        self.execute_window_push(
            query, program_session.exe_path, program_session.start_time.dt)

    def select_where_time_equals_for_session(self, some_time, target_exe_path):
        return select(DailyProgramSummary).where(
            DailyProgramSummary.exe_path_as_id == target_exe_path,
            DailyProgramSummary.gathering_date.op('=')(some_time)
        )

    def add_used_time(self, session: ProgramSession, duration_in_sec: int):
        """
        When a session is concluded, it was concluded partway thru the 10 sec window

        9 times out of 10. So we add  the used  duration from its hours_spent.
        """
        self.add_partial_window(
            session, duration_in_sec, DailyProgramSummary.exe_path_as_id == session.exe_path)

    async def shutdown(self):
        """Closes the open session without opening a new one"""

        pass

    def close(self):
        if hasattr(self, '_current_session') and self._current_session is not None:
            self._current_session.close()
            self._current_session = None
