from datetime import datetime

from activitytracker.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from activitytracker.db.dao.direct.program_summary_dao import ProgramSummaryDao
from activitytracker.db.dao.direct.video_summary_dao import VideoSummaryDao
from activitytracker.db.dao.queuing.chrome_logs_dao import ChromeLoggingDao
from activitytracker.db.dao.queuing.program_logs_dao import ProgramLoggingDao
from activitytracker.db.dao.queuing.video_logs_dao import VideoLoggingDao
from activitytracker.object.arbiter_classes import InternalState
from activitytracker.object.classes import (
    ChromeSession,
    CompletedChromeSession,
    CompletedProgramSession,
    ProgramSession,
    VideoSession,
)
from activitytracker.tz_handling.time_formatting import get_start_of_day_from_ult
from activitytracker.util.clock import UserFacingClock
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.time_wrappers import UserLocalTime

# Persistence component


class ActivityRecorder:
    def __init__(
        self,
        program_logging_dao: ProgramLoggingDao,
        chrome_logging_dao: ChromeLoggingDao,
        video_logging_dao: VideoLoggingDao,
        program_summary_dao: ProgramSummaryDao,
        chrome_summary_dao: ChromeSummaryDao,
        video_summary_dao: VideoSummaryDao,
        DEBUG=False,
    ):
        self.program_logging_dao = program_logging_dao
        self.chrome_logging_dao = chrome_logging_dao
        self.video_logging_dao = video_logging_dao
        self.program_summary_dao = program_summary_dao
        self.chrome_summary_dao = chrome_summary_dao
        self.video_summary_dao = video_summary_dao
        self.DEBUG = DEBUG
        self.logger = ConsoleLogger()
        if not DEBUG:
            self.logger.log_yellow("Recorder logs are off")

        # For testing: collect session activity history
        # List of (session, timestamp) tuples for each pulse
        self.pulse_history = []
        # List of (session, amount, timestamp) tuples for each deduction
        self.remainder_history = []

    def on_new_session(self, session: ProgramSession | ChromeSession):
        # TODO: do an audit of logging time and summary time.
        if session.video_info:

            self.logger.log_video_info("on_new_session", session.video_info)
            video_session = VideoSession.from_other_type(session)

            self.video_logging_dao.start_session(video_session)

            session_exists_already = self.video_summary_dao.find_todays_entry_for_media(
                video_session
            )
            if not session_exists_already:
                self.video_summary_dao.start_session(video_session)
        if isinstance(session, ProgramSession):
            # Regardless of the session being brand new today or a repeat,
            # must start a new logging session, to note the time being added to the summary.
            self.program_logging_dao.start_session(session)
            session_exists_already = self.program_summary_dao.find_todays_entry_for_program(
                session
            )
            if session_exists_already:
                # After thinking about it longer, it makes much more sense for ALL additions of time
                # to flow through the KeepAliveEngine. That way, there's only one place to look for time being added.
                # self.program_summary_dao.start_window_push_for_session(session, now)
                return
            self.program_summary_dao.start_session(session)
        elif isinstance(session, ChromeSession):
            self.chrome_logging_dao.start_session(session)
            session_exists_already = self.chrome_summary_dao.find_todays_entry_for_domain(
                session
            )
            if session_exists_already:
                # self.chrome_summary_dao.start_window_push_for_session(session, now)
                return
            self.chrome_summary_dao.start_session(session)
        else:
            raise TypeError("Session was not the right type")

    def add_ten_sec_to_end_time(self, session: ProgramSession | ChromeSession):
        """
        Pushes the end of the window forward ten sec so that,
        when the computer shuts down, the end time was "about right" anyways.
        """
        if session is None:
            raise ValueError("Session was None in add_ten_sec")
        # For testing
        if self.DEBUG:
            self.pulse_history.append((session, session.start_time))
            session.ledger.add_ten_sec()

        # Window push now finds session based on start_time
        print(session.video_info, "-- in add ten sec")

        if session.video_info:
            self.logger.log_video_info("add_ten_sec_to_end_time", session.video_info)
            video_session = VideoSession.from_other_type(session)

            self.video_logging_dao.push_window_ahead_ten_sec(video_session)
            self.video_summary_dao.push_window_ahead_ten_sec(video_session)
        if isinstance(session, ProgramSession):
            self.program_logging_dao.push_window_ahead_ten_sec(session)
            self.program_summary_dao.push_window_ahead_ten_sec(session)
        elif isinstance(session, ChromeSession):
            self.chrome_logging_dao.push_window_ahead_ten_sec(session)
            self.chrome_summary_dao.push_window_ahead_ten_sec(session)
        else:
            raise TypeError("Session was not the right type")

    def add_partial_window(
        self, duration_in_sec: int, session: ProgramSession | ChromeSession
    ):
        """
        Deducts t seconds from the duration of a session.
        Here, the session's current window was cut short by a new session taking it's place.
        """
        if session.start_time is None:
            raise ValueError("Session start time was not set")

        # For testing: record this deduction
        if self.DEBUG:
            self.remainder_history.append((session, duration_in_sec, session.start_time))
            session.ledger.extend_by_n(duration_in_sec)
        if duration_in_sec == 0:
            return  # Nothing to add

        print(session.video_info, "-- in add partial window")

        if session.video_info:
            self.logger.log_video_info("add_partial_window", session.video_info)
            video_session = VideoSession.from_other_type(session)
            self.video_summary_dao.add_used_time(video_session, duration_in_sec)

        if isinstance(session, ProgramSession):
            self.program_summary_dao.add_used_time(session, duration_in_sec)
        elif isinstance(session, ChromeSession):
            self.chrome_summary_dao.add_used_time(session, duration_in_sec)
        else:
            raise TypeError("Session was not the right type")

    def on_state_changed(
        self, session: CompletedProgramSession | CompletedChromeSession | None
    ):
        if session is not None and session.video_info:
            self.logger.log_video_info("add_partial_window", session.video_info)
            video_session = VideoSession.from_other_type(session)
            completed_video_session = video_session.to_completed(session.end_time)
            self.video_logging_dao.finalize_log(completed_video_session)
        if isinstance(session, ProgramSession):
            self.program_logging_dao.finalize_log(session)
        elif isinstance(session, ChromeSession):
            self.chrome_logging_dao.finalize_log(session)
        else:
            if session is None:
                return
            raise TypeError("Session was not the right type")
