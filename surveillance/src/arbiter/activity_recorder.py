from ..object.classes import ChromeSessionData, ProgramSessionData
from ..object.arbiter_classes import InternalState

from ..db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from ..db.dao.direct.program_summary_dao import ProgramSummaryDao
from ..db.dao.queuing.program_logs_dao import ProgramLoggingDao
from ..db.dao.queuing.chrome_logs_dao import ChromeLoggingDao

# Persistence component


class ActivityRecorder:
    def __init__(self, user_facing_clock,program_logging_dao: ProgramLoggingDao, chrome_logging_dao:ChromeLoggingDao, program_summary_dao: ProgramSummaryDao, chrome_summary_dao: ChromeSummaryDao):
        self.user_facing_clock = user_facing_clock
        self.program_logging_dao = program_logging_dao
        self.chrome_logging_dao = chrome_logging_dao
        self.program_summary_dao = program_summary_dao
        self.chrome_summary_dao = chrome_summary_dao 

    def validate_session(self, session):
        if session.end_time is None:
            raise ValueError("Session end time was not set")
        if session.duration is None:
            raise ValueError("Session duration was not set")
        
    def on_new_session(self, session: ProgramSessionData | ChromeSessionData):
        """
        This exists because some code I expected to start a log
        before any other code asked to update the log, did not create
        the log as expected. And so I am doing it manually.
        In hindsight "add_ten_sec_to_end_time" doesn't really scream "creates the log file".
        """
        if isinstance(session, ProgramSessionData):
            # TODO: Store actibve sessions IDs in a cache so don't have to .find_session() over & over
            # session_exists = self.program_logging_dao.find_session(session)
            # if session_exists:
            #     return
            self.program_logging_dao.start_session(session)
        elif isinstance(session, ChromeSessionData):
            # TODO: Store actibve sessions IDs in a cache so don't have to .find_session() over & over
            # session_exists = self.chrome_logging_dao.find_session(session)
            # if session_exists:
            #     return
            self.chrome_logging_dao.start_session(session)
        else:
            raise TypeError("Session was not the right type")

    def on_state_changed(self, session):
        if isinstance(session, ProgramSessionData):
            self.validate_session(session)
            self.program_logging_dao.finalize_log(session)
        elif isinstance(session, ChromeSessionData):
            self.validate_session(session)
            self.chrome_logging_dao.finalize_log(session)
        else:
            if isinstance(session, InternalState):
                raise TypeError(
                    "Argument was an InternalState when it should be a Session")
            raise TypeError("Session was not the right type")

    def add_ten_sec_to_end_time(self, session):
        """
        Pushes the end of the window forward ten sec so that, 
        when the computer shuts down, the end time was "about right" anyways.
        """
        print("Add ten sec was reached")
        print("Update or create log! 49ru")
        if isinstance(session, ProgramSessionData):
            self.program_logging_dao.push_window_ahead_ten_sec(session)
            self.program_summary_dao.push_window_ahead_ten_sec(session)
        elif isinstance(session, ChromeSessionData):
            self.chrome_logging_dao.push_window_ahead_ten_sec(session)
            self.chrome_summary_dao.push_window_ahead_ten_sec(session)
        else:
            raise TypeError("Session was not the right type")
        
    # async def update_or_create_log(self, logging_dao: ProgramLoggingDao | ChromeLoggingDao, session):
    #     # Note that the cost of the read in find_session occurs 
    #     # once per 8 ish sec, which is a very low cost
    #     session_exists = await logging_dao.find_session(session)

    #     if session_exists:
    #         print("Session exists!")
            
    #     else:
    #         print("starting session!")
    #         await logging_dao.start_session(session)

    def deduct_duration(self, duration_in_sec: int, session):
        """
        Deducts t seconds from the duration of a session. 
        Here, the session's current window was cut short by a new session taking it's place.
        """
        today_start = self.user_facing_clock.today_start()
        if isinstance(session, ProgramSessionData):
            self.program_summary_dao.deduct_remaining_duration(session, duration_in_sec, today_start)
        elif isinstance(session, ChromeSessionData):
            self.chrome_summary_dao.deduct_remaining_duration(session, duration_in_sec, today_start)
        else:
            raise TypeError("Session was not the right type")
