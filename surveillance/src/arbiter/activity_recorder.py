from ..object.classes import ChromeSessionData, ProgramSessionData
from ..object.arbiter_classes import InternalState

# Persistence component


class ActivityRecorder:
    def __init__(self, user_facing_clock, program_summary_dao, chrome_summary_dao):
        self.user_facing_clock = user_facing_clock
        self.program_summary_dao = program_summary_dao
        self.chrome_summary_dao = chrome_summary_dao

    async def on_state_changed(self, session, is_shutdown=False):
        if isinstance(session, InternalState):
            print(session)
            raise TypeError(
                "Argument was an InternalState when it should be a Session")
        if session.end_time is None:
            print(session)
            raise ValueError("Session end time was not set")
        if session.duration is None:
            raise ValueError("Session duration was not set")

        right_now = self.user_facing_clock.now()

        if isinstance(session, ChromeSessionData):
            await self.chrome_summary_dao.create_if_new_else_update(session, right_now, is_shutdown)
        elif isinstance(session, ProgramSessionData):
            await self.program_summary_dao.create_if_new_else_update(session, right_now, is_shutdown)
        else:
            raise TypeError("Session was not the right type")

    async def add_ten_sec_to_end_time(self, session):
        """
        Pushes the end of the window forward ten sec so that, 
        when the computer shuts down, the end time was "about right" anyways.
        """
        pass

    async def deduct_duration(self, duration, session):
        """
        Deducts t seconds from the duration of a session. 
        Here, the session's current window was cut short by a new session taking it's place.
        """
        pass