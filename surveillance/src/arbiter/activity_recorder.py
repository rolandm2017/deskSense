from ..object.classes import ChromeSessionData, ProgramSessionData
from ..object.arbiter_classes import InternalState

# Persistence component


class ActivityRecorder:
    def __init__(self, program_summary_dao, chrome_summary_dao):
        self.program_summary_dao = program_summary_dao
        self.chrome_summary_dao = chrome_summary_dao

    async def on_state_changed(self, state):
        if not isinstance(state, InternalState):
            print(state)
            raise TypeError("Argument was not InternalState")
        if state.session.end_time is None:
            print(state)
            raise ValueError("Session end time was not set")
        old_session = state.session

        if isinstance(old_session, ChromeSessionData):
            await self.chrome_summary_dao.create_if_new_else_update(old_session)
        else:
            await self.program_summary_dao.create_if_new_else_update(old_session)
