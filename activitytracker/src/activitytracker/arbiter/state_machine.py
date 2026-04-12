from datetime import timedelta

from activitytracker.object.arbiter_classes import (
    ApplicationInternalState,
    ChromeInternalState,
    InternalState,
)
from activitytracker.object.classes import (
    ChromeSession,
    CompletedChromeSession,
    CompletedProgramSession,
    ProgramSession,
)
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.copy_util import snapshot_obj_for_tests
from activitytracker.util.errors import SuspiciousDurationError
from activitytracker.util.program_tools import window_is_chrome
from activitytracker.util.time_wrappers import UserLocalTime


class StateMachine:
    def __init__(self, user_facing_clock):
        """
        Is a finite state machine.

        One instance per user. Meaning, state from User A has no reason to interact with User B's state.
        """
        self.user_facing_clock = user_facing_clock
        self.current_state: InternalState | None = None
        self.state_listeners = []
        self.logger = ConsoleLogger()

    def set_new_session(
        self,
        next_session: ProgramSession | ChromeSession,
    ) -> CompletedProgramSession | CompletedChromeSession | None:
        # FIXME: Isn't this JUST handing off one session to the other now?
        # FIXME: Existing just to do, "end_time - start_time" and such
        next_session = snapshot_obj_for_tests(next_session)
        if self.current_state is None:
            # No current state yet, this is initialization:
            updated_state = InternalState(None, None, next_session)
            self.current_state = updated_state
            return None

        concluded = self._build_concluded(self.current_state, next_session.start_time)
        self.current_state = InternalState(None, None, next_session)
        return concluded

    def _build_concluded(
        self,
        state: InternalState,
        incoming_session_start: UserLocalTime,
    ) -> CompletedProgramSession | CompletedChromeSession | None:
        """Conclude the current session. Returns the completed session or None."""
        if not isinstance(incoming_session_start, UserLocalTime):
            raise ValueError("Expected a UserLocalTime")
        if self.is_initialization_session(state.session):
            return None

        duration = incoming_session_start.dt - state.session.start_time.dt
        # FIXME: "concluding session:  9:42:51.327057" after overnight sleep
        # FIXME: Solution to above problem is to check the latest
        # keepAlive write time, the latest um, systemStatus polling write time.
        # If the latest write was more than a minute ago, the session is over,
        # do not update the end time past that time.
        print("concluding session: ", duration)
        if duration.total_seconds() < -60:
            # One minute in seconds
            print("Outgoing session: ", state.session)
            print("Inc session start:", incoming_session_start)
            raise SuspiciousDurationError("Negative duration")

        session_copy = snapshot_obj_for_tests(state.session)

        # FIXME: (1) This whole file can go. It's just a session container.

        # FIXME: Durations are negative sometimes
        # TODO: Make toCompleted throw err if end time before start time
        completed = session_copy.to_completed(incoming_session_start)
        completed.duration = duration
        return completed

    def _conclude_session(
        self,
        state: InternalState,
        incoming_session_start: UserLocalTime,
    ):
        completed = self._build_concluded(state, incoming_session_start)
        if completed is not None:
            state.session = completed

    def conclude_without_replacement_at_time(self, given_time: UserLocalTime):
        if self.current_state is None:
            raise ValueError("Expected a current state")
        self._conclude_session(self.current_state, given_time)
        session_for_daos = self.current_state.session
        self.current_state = None  # Reset loop state
        return session_for_daos

    def conclude_without_replacement(self):
        """For wrap up when the computer is powering off to avoid sessions left open"""
        if self.current_state is None:
            return  # Nothing to wrap up
        end_time = UserLocalTime(self.user_facing_clock.now())
        assert isinstance(end_time, UserLocalTime)
        self._conclude_session(self.current_state, end_time)
        session_for_daos = self.current_state.session
        self.current_state = None  # Reset for power back on
        return session_for_daos

    @staticmethod
    def is_initialization_session(some_dict):
        """Asks 'is it an empty dict?'"""
        return isinstance(some_dict, dict) and not some_dict

    @staticmethod
    def _initialize(first_session):
        if isinstance(first_session, ProgramSession):
            is_chrome = window_is_chrome(first_session.window_title)
            updated_state = ApplicationInternalState(
                first_session.window_title, is_chrome, first_session
            )
        else:
            assert isinstance(first_session, ChromeSession)
            updated_state = ChromeInternalState(
                "Chrome", True, first_session.domain, first_session
            )
        return updated_state
