from ..object.classes import ChromeSessionData, ProgramSessionData

# Persistence component


class ActivityRecorder:
    def __init__(self, chrome_summary_dao, program_summary_dao):
        self.chrome_summary_dao = chrome_summary_dao
        self.program_summary_dao = program_summary_dao

    async def on_state_changed(self, previous_state, new_state):
        # Only handle persistence of the previous state
        if previous_state:
            old_session = previous_state.session
            if isinstance(old_session, ChromeSessionData):
                await self.chrome_summary_dao.create_if_new_else_update(old_session)
            else:
                await self.program_summary_dao.create_if_new_else_update(old_session)
