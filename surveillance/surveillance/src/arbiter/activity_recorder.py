from datetime import datetime

from surveillance.src.object.classes import ChromeSession, ProgramSession, CompletedChromeSession, CompletedProgramSession
from surveillance.src.object.arbiter_classes import InternalState

from surveillance.src.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from surveillance.src.db.dao.direct.program_summary_dao import ProgramSummaryDao
from surveillance.src.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao

from surveillance.src.util.clock import UserFacingClock
from surveillance.src.util.time_wrappers import UserLocalTime
from surveillance.src.util.time_formatting import get_start_of_day_from_ult



# Persistence component


class ActivityRecorder:
    def __init__(self, user_facing_clock: UserFacingClock, program_logging_dao: ProgramLoggingDao, chrome_logging_dao: ChromeLoggingDao, program_summary_dao: ProgramSummaryDao, chrome_summary_dao: ChromeSummaryDao):
        self.user_facing_clock = user_facing_clock
        self.program_logging_dao = program_logging_dao
        self.chrome_logging_dao = chrome_logging_dao
        self.program_summary_dao = program_summary_dao
        self.chrome_summary_dao = chrome_summary_dao

    @staticmethod
    def validate_session(session):
        if session.end_time is None:
            raise ValueError("Session end time was not set")
        if session.duration is None:
            raise ValueError("Session duration was not set")

    def on_new_session(self, session: ProgramSession | ChromeSession):
        """
        This exists because some code I expected to start a log
        before any other code asked to update the log, did not create
        the log as expected. And so I am doing it manually.
        """
        now = self.user_facing_clock.now()
        if isinstance(session, ProgramSession):
            # Must start a new logging session, to note the time being added to the summary. 
            # This addition happens whether the program is brand new today or was seen before
            self.program_logging_dao.start_session(session)
            session_exists_already = self.program_summary_dao.find_todays_entry_for_program(
                session)
            # TODO: After e2e tests, in assert phase, do an audit of logging time and summary time.
            if session_exists_already:
                self.program_summary_dao.start_window_push_for_session(session, now)
                return
            self.program_summary_dao.start_session(session, now)
        elif isinstance(session, ChromeSession):
            self.chrome_logging_dao.start_session(session)
            session_exists_already = self.chrome_summary_dao.find_todays_entry_for_domain(
                session)
            if session_exists_already:
                return
            self.chrome_summary_dao.start_session(session, now)
        else:
            raise TypeError("Session was not the right type")

    def add_ten_sec_to_end_time(self, session: ProgramSession | ChromeSession):
        """
        Pushes the end of the window forward ten sec so that, 
        when the computer shuts down, the end time was "about right" anyways.

        The session.start_time cannot serve as the source of time here, so the clock is used.
        """
        if session is None:
            raise ValueError("Session was None in add_ten_sec")
        now: UserLocalTime = self.user_facing_clock.now()
        if isinstance(session, ProgramSession):
            self.program_logging_dao.push_window_ahead_ten_sec(session)
            self.program_summary_dao.push_window_ahead_ten_sec(session, now)
        elif isinstance(session, ChromeSession):
            self.chrome_logging_dao.push_window_ahead_ten_sec(session)
            self.chrome_summary_dao.push_window_ahead_ten_sec(session, now)
        else:
            raise TypeError("Session was not the right type")

    def on_state_changed(self, session: CompletedProgramSession | CompletedChromeSession | None):
        if isinstance(session, ProgramSession):
            self.validate_session(session)
            self.program_logging_dao.finalize_log(session)
        elif isinstance(session, ChromeSession):
            self.validate_session(session)
            self.chrome_logging_dao.finalize_log(session)
        else:
            if session is None:
                return
            if isinstance(session, InternalState):
                raise TypeError(
                    "Argument was an InternalState when it should be a Session")
            raise TypeError("Session was not the right type")

    def deduct_duration(self, duration_in_sec: int, session: ProgramSession | ChromeSession):
        """
        Deducts t seconds from the duration of a session. 
        Here, the session's current window was cut short by a new session taking it's place.
        """
        if session.start_time is None:
            raise ValueError("Session start time was not set")
        today_start: UserLocalTime = get_start_of_day_from_ult(session.start_time)
        if isinstance(session, ProgramSession):
            print(
                f"deducting {duration_in_sec} from {session.window_title}")
            self.program_summary_dao.deduct_remaining_duration(
                session, duration_in_sec, today_start)
        elif isinstance(session, ChromeSession):
            print(f"deducting {duration_in_sec} from {session.domain}")
            self.chrome_summary_dao.deduct_remaining_duration(
                session, duration_in_sec, today_start)
        else:
            raise TypeError("Session was not the right type")
