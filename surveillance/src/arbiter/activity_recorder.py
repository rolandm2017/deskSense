from ..object.classes import ChromeSessionData, ProgramSessionData
from ..object.arbiter_classes import InternalState

# Persistence component


class ActivityRecorder:
    def __init__(self, user_facing_clock, program_summary_dao, chrome_summary_dao):
        self.user_facing_clock = user_facing_clock
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

        right_now = self.user_facing_clock.now()

        if isinstance(session, ChromeSessionData):
            await self.chrome_summary_dao.create_if_new_else_update(session, right_now)
        elif isinstance(session, ProgramSessionData):
            await self.program_summary_dao.create_if_new_else_update(session, right_now)
        else:
            raise TypeError("Session was not the right type")
