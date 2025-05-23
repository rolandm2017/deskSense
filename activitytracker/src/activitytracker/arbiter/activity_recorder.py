from datetime import datetime

from activitytracker.db.dao.direct.chrome_summary_dao import ChromeSummaryDao
from activitytracker.db.dao.direct.mystery_media_dao import MysteryMediaDao
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
from activitytracker.object.video_classes import NetflixInfo
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
        mystery_media_dao: MysteryMediaDao,
        DEBUG=False,
    ):
        self.program_logging_dao = program_logging_dao
        self.chrome_logging_dao = chrome_logging_dao
        self.video_logging_dao = video_logging_dao
        self.program_summary_dao = program_summary_dao
        self.chrome_summary_dao = chrome_summary_dao
        self.video_summary_dao = video_summary_dao
        self.mystery_media_dao = mystery_media_dao
        self.mystery_cache = NetflixMysteryCache()
        # On init, the cache is filled with the most recent 50 mysteries:
        most_recent_50 = mystery_media_dao.find_most_recent_fifty()
        self.mystery_cache.init(most_recent_50)

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
            if isinstance(video_session, NetflixInfo):
                if video_session.media_title is None:
                    video_session.media_title = self.handle_netflix_entry(video_session)
                else:
                    self.update_titles_if_mystery_title_found(video_session)

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
            if isinstance(video_session, NetflixInfo):
                if video_session.media_title is None:
                    video_session.media_title = self.handle_netflix_entry(video_session)
                else:
                    self.update_titles_if_mystery_title_found(video_session)

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
            video_session: VideoSession = VideoSession.from_other_type(session)
            if isinstance(video_session, NetflixInfo):
                if video_session.media_title is None:
                    video_session.media_title = self.handle_netflix_entry(video_session)
                else:
                    self.update_titles_if_mystery_title_found(video_session)
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

    def handle_netflix_entry(self, video_session: VideoSession) -> str | None:
        # First, look in the Summary DAO for the ID of the media.
        found_title = self.video_summary_dao.find_netflix_media_by_id(
            video_session.video_info.video_id
        )
        if found_title:
            return found_title
        else:
            # If it isn't there, put it in the Mystery Media table.
            self.mystery_media_dao.create(
                video_session.video_info.video_id, video_session.start_time
            )

    def update_titles_if_mystery_title_found(self, video_session: VideoSession):
        id_is_in_mysteries = self.mystery_cache.find_mysteries(
            video_session.video_info.video_id
        )
        if id_is_in_mysteries:
            # update summary DAO, logging DAOs for this ID with a name!
            self.video_summary_dao.update_name_for_mystery(
                video_session.video_info.video_id, video_session.get_name()
            )
            self.video_logging_dao.update_name_for_mystery(
                video_session.video_info.video_id, video_session.get_name()
            )
            self.mystery_cache.delete(video_session.video_info.video_id)
            self.mystery_media_dao.delete_by_id(video_session.video_info.video_id)

    def handle_mystery_id(self, mystery_id):
        """
        Situation: Program has the Video ID, but not the media name.
        """
        # If it's a recently discovered media title*, get it's name! and proceed like it's normal
        # * i.e. it exists in a very quick to query thing like a dict of video_id -> media title
        # If it isn't a recently discovered media title, put it in the mystery cache
        pass

    def handle_discovery_of_mystery_title(self, mystery_media_id):
        """
        When a Netflix title comes in, and the video ID associated with the title
        is in the Mystery Media Cache, (1) update all entries for that Video ID
        with the newly discovered media title. (2) Take it out of the cache
        """
        pass


class RecentNetflixTitlesCache:
    def __init__(self) -> None:
        self.recents = {}

    def add(self, key, title):
        """Don't worry about deleting old entries.
        Cache will likely be recreated every week or so by
        the computer being restarted, etc."""
        self.recents[key] = title

    def contains(self, key):
        return self.recents[key]


class NetflixMysteryCache:
    """An array of video IDs of recent mystery media (video IDs with unknown titles)"""

    def __init__(self) -> None:
        self.mysteries = []

    def init(self, top_fifty):
        self.mysteries = top_fifty

    def store_mystery(self, mystery_id):
        self.mysteries.append(mystery_id)

    def find_mysteries(self, known_media_id):
        return known_media_id in self.mysteries

    def delete(self, discovered_id):
        self.mysteries.remove(discovered_id)


# SO what I want is,
# ONE: For a netflix media, where only the ID is known, for it to be super fast to look up if it's associated
# with a title.

# TWO: To be able to store a mystery ID in such a way that it can be looked for very fast.

# THREE: When a Netflix Mystery ID's true title is discovered, the DAOs update the
# title names from "Unknown Media Title" to the true title.
