from surveillance.src.object.classes import ChromeSession, ProgramSession
from surveillance.src.object.arbiter_classes import InternalState

from surveillance.src.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from surveillance.src.db.dao.direct.program_summary_dao import ProgramSummaryDao
from surveillance.src.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from surveillance.src.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao

from surveillance.src.util.clock import UserFacingClock
from surveillance.src.util.time_wrappers import UserLocalTime

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
        In hindsight "add_ten_sec_to_end_time" doesn't really scream "creates the log file".
        """
        now = self.user_facing_clock.now()
        if isinstance(session, ProgramSession):
            self.program_logging_dao.start_session(session)
            session_exists = self.program_summary_dao.find_todays_entry_for_program(
                session)
            if session_exists:
                return
            self.program_summary_dao.start_session(session, now)
        elif isinstance(session, ChromeSession):
            print(f"FINDING {session.domain}")
            self.chrome_logging_dao.start_session(session)
            session_exists = self.chrome_summary_dao.find_todays_entry_for_domain(
                session)
            if session_exists:
                print(f"###\n### FOUND -> {session.domain}")
                return
            print(f"@ @ \n@ @ STARTING {session.domain}")
            self.chrome_summary_dao.start_session(session, now)
        else:
            raise TypeError("Session was not the right type")

    def add_ten_sec_to_end_time(self, session):
        """
        Pushes the end of the window forward ten sec so that, 
        when the computer shuts down, the end time was "about right" anyways.
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

    def on_state_changed(self, session):
        if isinstance(session, ProgramSession):
            self.validate_session(session)
            self.program_logging_dao.finalize_log(session)
        elif isinstance(session, ChromeSession):
            self.validate_session(session)
            self.chrome_logging_dao.finalize_log(session)
        else:
            if isinstance(session, InternalState):
                raise TypeError(
                    "Argument was an InternalState when it should be a Session")
            raise TypeError("Session was not the right type")

    def deduct_duration(self, duration_in_sec: int, session):
        """
        Deducts t seconds from the duration of a session. 
        Here, the session's current window was cut short by a new session taking it's place.
        """
        today_start = self.user_facing_clock.today_start()
        if isinstance(session, ProgramSession):
            # print(
            #     f"deducting {duration_in_sec} from {session.window_title}")
            self.program_summary_dao.deduct_remaining_duration(
                session, duration_in_sec, today_start)
        elif isinstance(session, ChromeSession):
            # print(f"deducting {duration_in_sec} from {session.domain}")
            self.chrome_summary_dao.deduct_remaining_duration(
                session, duration_in_sec, today_start)
        else:
            raise TypeError("Session was not the right type")
