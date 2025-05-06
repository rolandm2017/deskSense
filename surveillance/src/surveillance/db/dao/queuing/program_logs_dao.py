
from sqlalchemy import select, or_
from sqlalchemy.orm import sessionmaker
from datetime import timedelta, datetime, date, timezone
from typing import List

from surveillance.db.dao.utility_dao_mixin import UtilityDaoMixin
from surveillance.db.dao.logging_dao_mixin import LoggingDaoMixin
from surveillance.db.models import ProgramSummaryLog

from surveillance.tz_handling.dao_objects import LogTimeConverter
from surveillance.object.classes import ProgramSession, CompletedProgramSession

from surveillance.util.console_logger import ConsoleLogger
from surveillance.util.errors import ImpossibleToGetHereError
from surveillance.util.arg_type_wrapper import validate_session, guarantee_start_time
from surveillance.util.log_dao_helper import convert_start_end_times_to_hours, convert_duration_to_hours
from surveillance.tz_handling.time_formatting import convert_to_utc, get_start_of_day_from_datetime, attach_tz_to_all
from surveillance.util.const import ten_sec_as_pct_of_hour
from surveillance.util.time_wrappers import UserLocalTime
from surveillance.util.log_dao_helper import group_logs_by_name


#
# #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
# #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
#


class ProgramLoggingDao(LoggingDaoMixin, UtilityDaoMixin):
    """DAO for program activity logging. 
    TIMEZONE HANDLING:
    - All datetimes are stored in UTC by PostgreSQL
    - Methods return UTC timestamps regardless of input timezone
    - Input datetimes should be timezone-aware
    - Date comparisons are performed in UTC"""

    def __init__(self, session_maker: sessionmaker):
        """ Exists mostly for debugging. """
        self.regular_session = session_maker  # Do not delete. UtilityDao still uses it
        self.logger = ConsoleLogger()
        self.model = ProgramSummaryLog

    def start_session(self, session: ProgramSession):
        """
        A session of using a domain. End_time here is like, "when did the user tab away from the program?"
        """
        # self.logger.log_white_multiple(
        #     "INFO: starting session for ", session.window_title)
        if session.start_time is None:
            raise ValueError("Start time was None")
        initializer = LogTimeConverter(session.start_time)

        # self.logger.log_white(f"INFO: starting session at start_of_day: {start_of_day_as_utc}\n\t for {session.process_name}")

        log_entry = ProgramSummaryLog(
            exe_path_as_id=session.exe_path,
            process_name=session.process_name,
            program_name=session.window_title,
            # Assumes (10 - n) sec will be deducted later
            # FIXME: all time additions should happen thru KeepAlive
            hours_spent=ten_sec_as_pct_of_hour,
            start_time=initializer.base_start_time_as_utc,
            start_time_local=session.start_time.dt,
            end_time=initializer.base_start_window_end,
            end_time_local=initializer.base_start_window_end.replace(
                tzinfo=None),
            duration_in_sec=0,
            gathering_date=initializer.start_of_day_as_utc,
            gathering_date_local=initializer.start_of_day_as_utc.replace(
                tzinfo=None),
            created_at=initializer.base_start_time_as_utc
        )
        # self.do_add_entry(log_entry)
        self.add_new_item(log_entry)

    def find_session(self, session: ProgramSession) -> ProgramSummaryLog | None:
        """Is finding it by time! Looking for the one, specifically, with the arg's time"""
        # the database is storing and returning times in UTC
        if session.start_time is None:
            raise ValueError("Start time was None")
        start_time_as_utc = convert_to_utc(
            session.start_time.get_dt_for_db())
        query = self.select_where_time_equals(start_time_as_utc)
        return self.execute_and_read_one_or_none(query)

    def select_where_time_equals(self, some_time):
        return select(ProgramSummaryLog).where(
            ProgramSummaryLog.start_time.op('=')(some_time)
        )

    def read_day_as_sorted(self, day: UserLocalTime) -> dict[str, ProgramSummaryLog]:
        # NOTE: the database is storing and returning times in UTC
        return self._read_day_as_sorted(day, ProgramSummaryLog, ProgramSummaryLog.program_name)

    def read_all(self) -> List[ProgramSummaryLog]:
        """Fetch all program log entries"""
        query = select(ProgramSummaryLog)
        # Developer is trusted to attach tz info manually
        return self.execute_and_return_all(query)

    def read_last_24_hrs(self, right_now: UserLocalTime):
        """Fetch all program log entries from the last 24 hours

        The database is storing and returning times in UTC btw
        """
        return self.do_read_last_24_hrs(right_now)

    def read_suspicious_entries(self):
        """Get entries with durations longer than 20 minutes"""
        suspicious_duration = 0.33333333  # 20 minutes in hours
        query = select(ProgramSummaryLog).where(
            ProgramSummaryLog.hours_spent > suspicious_duration
        ).order_by(ProgramSummaryLog.hours_spent.desc())
        return self.execute_and_return_all(query)

    def read_suspicious_alt_tab_windows(self):
        """Get alt-tab windows with durations longer than 10 seconds"""
        alt_tab_threshold = 0.0027777  # 10 seconds in hours, or 10/3600
        query = select(ProgramSummaryLog).where(
            ProgramSummaryLog.program_name == "Alt-tab window",
            ProgramSummaryLog.hours_spent > alt_tab_threshold
        ).order_by(ProgramSummaryLog.hours_spent.desc())
        return self.execute_and_return_all(query)

    def push_window_ahead_ten_sec(self, session: ProgramSession):
        if session is None:
            raise ValueError("Session was None")
        log: ProgramSummaryLog = self.find_session(session)
        if not log:
            raise ImpossibleToGetHereError(
                "Start of pulse didn't reach the db")
        log.duration_in_sec = log.duration_in_sec + 10
        log.end_time = log.end_time + timedelta(seconds=10)
        self.update_item(log)

    def finalize_log(self, session: CompletedProgramSession):
        """Overwrite value from the pulse. Expect something to ALWAYS be in the db already at this point."""
        log: ProgramSummaryLog = self.find_session(session)
        if not log:
            raise ImpossibleToGetHereError(
                "Start of pulse didn't reach the db")
        self.attach_final_values_and_update(session, log)
