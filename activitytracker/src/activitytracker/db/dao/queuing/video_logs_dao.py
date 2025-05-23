import asyncio
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker

from datetime import date, datetime, timedelta, timezone

from typing import List

from activitytracker.db.dao.logging_dao_mixin import LoggingDaoMixin
from activitytracker.db.dao.utility_dao_mixin import UtilityDaoMixin
from activitytracker.db.models import VideoSummaryLog
from activitytracker.object.classes import (
    CompletedVideoSession,
    VideoInfo,
    VideoSession,
)
from activitytracker.tz_handling.dao_objects import LogTimeConverter
from activitytracker.tz_handling.time_formatting import (
    attach_tz_to_all,
    convert_to_utc,
    get_start_of_day_from_datetime,
    get_start_of_day_from_ult,
)
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.const import ten_sec_as_pct_of_hour
from activitytracker.util.errors import ImpossibleToGetHereError
from activitytracker.util.log_dao_helper import (
    convert_duration_to_hours,
    convert_start_end_times_to_hours,
    group_logs_by_name,
)
from activitytracker.util.time_wrappers import UserLocalTime

#
# #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
# #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
#


class VideoLoggingDao(LoggingDaoMixin, UtilityDaoMixin):
    """DAO for program activity logging.
    TIMEZONE HANDLING:
    - All datetimes are stored in UTC by PostgreSQL
    - Methods return UTC timestamps regardless of input timezone
    - Input datetimes should be timezone-aware
    - Date comparisons are performed in UTC"""

    def __init__(self, session_maker: sessionmaker):
        """Exists mostly for debugging."""

        self.regular_session = session_maker  # Do not delete. UtilityDao still uses it
        self.logger = ConsoleLogger()
        self.model = VideoSummaryLog

    def start_session(self, session: VideoSession):
        """
        A session of using a domain. End_time here is like, "when did the user tab away from the program?"

        Remember that Video is double counted on purpose!
        """

        initializer = LogTimeConverter(session.start_time)

        log_entry = VideoSummaryLog(
            video_id=session.video_info.video_id,
            media_name=session.media_title,
            platform=session.video_info.get_platform_title(),
            # Assumes n sec will be added later
            hours_spent=0,
            start_time=initializer.base_start_time_as_utc,
            start_time_local=session.start_time.dt,
            end_time=initializer.base_start_window_end,
            end_time_local=initializer.base_start_window_end.replace(tzinfo=None),
            duration_in_sec=0,
            gathering_date=initializer.start_of_day_as_utc,
            gathering_date_local=initializer.start_of_day_as_utc.replace(tzinfo=None),
            created_at=initializer.base_start_time_as_utc,
        )
        self.add_new_item(log_entry)

    def find_session(self, session: VideoSession):
        """Is finding it by time! Looking for the one, specifically, with the arg's time"""
        if session.start_time is None:
            raise ValueError("Start time was None")
        start_time_as_utc = convert_to_utc(session.start_time.get_dt_for_db())
        query = self.select_where_time_equals(start_time_as_utc)

        return self.execute_and_read_one_or_none(query)

    def select_where_time_equals(self, some_time):
        return select(VideoSummaryLog).where(VideoSummaryLog.start_time.op("=")(some_time))

    def read_day_as_sorted(self, day: UserLocalTime) -> dict[str, VideoSummaryLog]:
        # NOTE: the database is storing and returning times in UTC
        return self._read_day_as_sorted(day, VideoSummaryLog, VideoSummaryLog.domain_name)

    def read_all(self) -> List[VideoSummaryLog]:
        """Fetch all domain log entries"""
        query = select(VideoSummaryLog)
        results = self.execute_and_return_all(query)
        return results  # Developer is trusted to attach tz manually where relevant
        # return self.execute_and_return_all(query)

    def read_last_24_hrs(self, right_now: UserLocalTime):
        """Fetch all domain log entries from the last 24 hours"""
        return self.do_read_last_24_hrs(right_now)

    def update_name_for_mystery(
        self, previously_mysterious_id: str, discovered_media_title: str
    ) -> None:
        """Update the discovered_name field for a MysteryMedia record with the given mystery_id"""
        with self.regular_session() as db_session:
            # Find the mystery media record by mystery_id
            mystery_media = db_session.scalars(
                select(self.model).where(
                    self.model.video_id == previously_mysterious_id,
                    # "Unknown Watch Page" is a magic string from the client
                    self.model.media_name == "Unknown Watch Page",
                )
            )

            if mystery_media:
                for media in mystery_media:
                    media.media_name = discovered_media_title
                db_session.commit()
            else:
                # Log or handle the case where no record is found
                self.logger.log_white(
                    f"[warning] No DailyVideoSummary found with previously_mysterious_id: {previously_mysterious_id}"
                )

    def push_window_ahead_ten_sec(self, session: VideoSession):
        log: VideoSummaryLog = self.find_session(session)
        if not log:
            raise ImpossibleToGetHereError("Start of pulse didn't reach the db")
        log.end_time = log.end_time + timedelta(seconds=10)
        self.update_item(log)

    def finalize_log(self, session: CompletedVideoSession):
        """
        Overwrite value from the pulse. Expect something to ALWAYS be in the db already at this point.
        Note that if the computer was shutdown, this method is never called, and the rough estimate is kept.
        """
        log: VideoSummaryLog = self.find_session(session)
        if not log:
            raise ImpossibleToGetHereError("Start of pulse didn't reach the db")
        self.attach_final_values_and_update(session, log)
