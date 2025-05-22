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
        self.prior_state: InternalState | None = None
        self.state_listeners = []
        self.logger = ConsoleLogger()

    def set_new_session(
        self,
        next_session: ProgramSession | ChromeSession,
        latest_status_write: UserLocalTime | None,
    ):
        # FIXME: Isn't this JUST handing off one session to the other now?
        # FIXME: Existing just to do, "end_time - start_time" and such
        next_session = snapshot_obj_for_tests(next_session)
        if self.current_state:
            updated_state = InternalState(None, None, next_session)
            if next_session.start_time:
                # Need: self.current_state.session. Nothin' else
                self._conclude_session(
                    self.current_state, next_session.start_time, latest_status_write
                )
                self.prior_state = self.current_state
                self.current_state = updated_state
            else:
                print("Error:", next_session)
                raise ValueError("Session start time was None")

        else:
            # No current state yet, this is initialization:
            if isinstance(next_session, ProgramSession):
                is_chrome = window_is_chrome(next_session.window_title)
                updated_state = ApplicationInternalState(
                    next_session.window_title, is_chrome, next_session
                )
            else:
                updated_state = ChromeInternalState(
                    "Chrome", True, next_session.domain, next_session
                )
            self.current_state = updated_state

    @staticmethod
    def is_initialization_session(some_dict):
        """Asks 'is it an empty dict?'"""
        return isinstance(some_dict, dict) and not some_dict

    def _conclude_session(
        self,
        state: InternalState,
        incoming_session_start: UserLocalTime,
        latest_status_write: UserLocalTime | None,
    ):
        if not isinstance(incoming_session_start, UserLocalTime):
            raise ValueError("Expected a UserLocalTime")
        if self.is_initialization_session(state.session):
            return

        # TODO: something like, "systemStatus.check_latest_write_time" here

        if (
            latest_status_write
            and latest_status_write.dt < incoming_session_start + timedelta(minutes=2)
        ):
            time_since_latest_write = (
                latest_status_write.dt - incoming_session_start.dt
            ).total_seconds() / 60
            self.logger.log_yellow(
                f"[warn] latest status write was {time_since_latest_write:2f} min ago"
            )
            # TODO: Put this block way up there. Should be a totally different concluder method.

        duration = incoming_session_start - state.session.start_time
        # FIXME: "concluding session:  9:42:51.327057" after overnight sleep
        # FIXME: Solution to above problem is to check the latest
        # keepAlive write time, the latest um, systemStatus polling write time.
        # If the latest write was more than a minute ago, the session is over,
        # do not update the end time past that time.
        print("concluding session: ", duration)

        session_copy = snapshot_obj_for_tests(state.session)

        # FIXME: (1) This whole file can go. It's just a session container.

        # FIXME: Durations are negative sometimes

        completed = session_copy.to_completed(incoming_session_start)
        completed.duration = duration

        state.session = completed

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

    def get_concluded_session(
        self,
    ) -> CompletedProgramSession | CompletedChromeSession | None:
        """Assumes the prior state is the updated transformation from set_new_session"""
        on_initialization = self.prior_state is None
        if on_initialization:
            return None
        assert self.prior_state is not None
        return self.prior_state.session

    def conclude_without_replacement_at_time(self, given_time: UserLocalTime):
        if self.current_state is None:
            raise ValueError("Expected a current state")
        self._conclude_session(self.current_state, given_time, given_time)
        session_for_daos = self.current_state.session
        self.current_state = None  # Reset loop state
        return session_for_daos

    def conclude_without_replacement(self):
        """For wrap up when the computer is powering off to avoid sessions left open"""
        if self.current_state is None:
            return  # Nothing to wrap up
        end_time = UserLocalTime(self.user_facing_clock.now())
        assert isinstance(end_time, UserLocalTime)
        self._conclude_session(self.current_state, end_time, end_time)
        session_for_daos = self.current_state.session
        self.current_state = None  # Reset for power back on
        return session_for_daos
