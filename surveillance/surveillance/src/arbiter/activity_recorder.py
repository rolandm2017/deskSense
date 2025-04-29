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

        # For testing: collect session activity history
        self.pulse_history = []  # List of (session, timestamp) tuples for each pulse
        self.remainder_history = []  # List of (session, amount, timestamp) tuples for each deduction

    def on_new_session(self, session: ProgramSession | ChromeSession):
        # TODO: do an audit of logging time and summary time.
        if isinstance(session, ProgramSession):
            # Regardless of the session being brand new today or a repeat,
            # must start a new logging session, to note the time being added to the summary. 
            self.program_logging_dao.start_session(session)
            session_exists_already = self.program_summary_dao.find_todays_entry_for_program(
                session)
            if session_exists_already:
                # After thinking about it longer, it makes much more sense for all additions of time
                # to flow through the KeepAliveEngine. That way, there's only one place to look for time being added.
                # self.program_summary_dao.start_window_push_for_session(session, now)
                return
            self.program_summary_dao.start_session(session, session.start_time)
        elif isinstance(session, ChromeSession):
            self.chrome_logging_dao.start_session(session)
            session_exists_already = self.chrome_summary_dao.find_todays_entry_for_domain(
                session)
            if session_exists_already:
                # self.chrome_summary_dao.start_window_push_for_session(session, now)
                return 
            self.chrome_summary_dao.start_session(session, session.start_time)
        else:
            raise TypeError("Session was not the right type")

    def add_ten_sec_to_end_time(self, session: ProgramSession | ChromeSession):
        """
        Pushes the end of the window forward ten sec so that, 
        when the computer shuts down, the end time was "about right" anyways.
        """
        if session is None:
            raise ValueError("Session was None in add_ten_sec")
        now: UserLocalTime = self.user_facing_clock.now()

        # For testing
        self.pulse_history.append((session, session.start_time))
        session.ledger.add_ten_sec()

        if isinstance(session, ProgramSession):
            self.program_logging_dao.push_window_ahead_ten_sec(session)
            self.program_summary_dao.push_window_ahead_ten_sec(session, now)
        elif isinstance(session, ChromeSession):
            self.chrome_logging_dao.push_window_ahead_ten_sec(session)
            self.chrome_summary_dao.push_window_ahead_ten_sec(session, now)
        else:
            raise TypeError("Session was not the right type")
    
    def add_partial_window(self, duration_in_sec: int, session: ProgramSession | ChromeSession):
        """
        Deducts t seconds from the duration of a session. 
        Here, the session's current window was cut short by a new session taking it's place.
        """
        if session.start_time is None:
            raise ValueError("Session start time was not set")
        today_start: UserLocalTime = get_start_of_day_from_ult(session.start_time)

        # For testing: record this deduction
        self.remainder_history.append((session, duration_in_sec, session.start_time))
        session.ledger.extend_by_n(duration_in_sec)

        if duration_in_sec == 0:
            return  # Nothing to add

        if isinstance(session, ProgramSession):
            print(
                f"adding {duration_in_sec} to {session.window_title}")
            self.program_summary_dao.add_used_time(
                session, duration_in_sec, today_start)
        elif isinstance(session, ChromeSession):
            print(f"adding {duration_in_sec} to {session.domain}")
            self.chrome_summary_dao.add_used_time(
                session, duration_in_sec, today_start)
        else:
            raise TypeError("Session was not the right type")

    def on_state_changed(self, session: CompletedProgramSession | CompletedChromeSession | None):
        if isinstance(session, ProgramSession):
            self.program_logging_dao.finalize_log(session)
        elif isinstance(session, ChromeSession):
            self.chrome_logging_dao.finalize_log(session)
        else:
            if session is None:
                return
            raise TypeError("Session was not the right type")
