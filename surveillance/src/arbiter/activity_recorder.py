from ..object.classes import ChromeSessionData, ProgramSessionData
from ..object.arbiter_classes import InternalState

from ..db.dao.chrome_summary_dao import ChromeSummaryDao
from ..db.dao.program_summary_dao import ProgramSummaryDao
from ..db.dao.summary_logs_dao import ProgramLoggingDao, ChromeLoggingDao

# Persistence component


class ActivityRecorder:
    def __init__(self, user_facing_clock,program_logging_dao: ProgramLoggingDao, chrome_logging_dao:ChromeLoggingDao, program_summary_dao: ProgramSummaryDao, chrome_summary_dao: ChromeSummaryDao):
        self.user_facing_clock = user_facing_clock
        self.program_logging_dao = program_logging_dao
        self.chrome_logging_dao = chrome_logging_dao
        self.program_summary_dao = program_summary_dao
        self.chrome_summary_dao = chrome_summary_dao 

    async def on_state_changed(self, session):
        if isinstance(session, InternalState):
            print(session)
            raise TypeError(
                "Argument was an InternalState when it should be a Session")
        if session.end_time is None:
            print(session)
            raise ValueError("Session end time was not set")
        if session.duration is None:
            raise ValueError("Session duration was not set")

        if isinstance(session, ProgramSessionData):
            await self.program_logging_dao.finalize_log(session)
            # await self.program_logging_dao.create_log(session, right_now)
            # await self.program_summary_dao.create_if_new_else_update(session, right_now)
        elif isinstance(session, ChromeSessionData):
            await self.chrome_logging_dao.finalize_log(session)
            # await self.chrome_logging_dao.create_log(session, right_now)
            # await self.chrome_summary_dao.create_if_new_else_update(session, right_now)
        else:
            raise TypeError("Session was not the right type")

    async def add_ten_sec_to_end_time(self, session):
        """
        Pushes the end of the window forward ten sec so that, 
        when the computer shuts down, the end time was "about right" anyways.
        """
        if isinstance(session, ProgramSessionData):
            self.update_or_create_log(self.program_logging_dao, session)
            await self.program_summary_dao.push_window_ahead_ten_sec(session)
        elif isinstance(session, ChromeSessionData):
            self.update_or_create_log(self.chrome_logging_dao, session)
            await self.chrome_summary_dao.push_window_ahead_ten_sec(session)
        else:
            raise TypeError("Session was not the right type")
        
    async def update_or_create_log(self, logging_dao: ProgramLoggingDao | ChromeLoggingDao, session):
        # Note that the cost of the read in find_session occurs 
        # once per 8 ish sec, which is a very low cost
        if logging_dao.find_session(session):
            await logging_dao.push_window_ahead_ten_sec(session)
        else:
            await logging_dao.start_session(session)

    async def deduct_duration(self, duration, session):
        """
        Deducts t seconds from the duration of a session. 
        Here, the session's current window was cut short by a new session taking it's place.
        """
        today_start = self.user_facing_clock.today_start()
        if isinstance(session, ProgramSessionData):
            # await self.program_summary_dao.do_the_remaining_work(session, right_now)
            await self.program_summary_dao.deduct_remaining_duration(session, duration, today_start)
        elif isinstance(session, ChromeSessionData):
            # await self.chrome_summary_dao.do_the_remaining_work(session, right_now)
            await self.chrome_summary_dao.deduct_remaining_duration(session, duration, today_start)
        else:
            raise TypeError("Session was not the right type")
