# video_summary_dao.py
from sqlalchemy import func, select, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.selectable import Select

from datetime import datetime, time, timedelta

from typing import List

from activitytracker.config.definitions import (
    keep_alive_cycle_length,
    window_push_length,
)
from activitytracker.db.dao.summary_dao_mixin import SummaryDaoMixin
from activitytracker.db.dao.utility_dao_mixin import UtilityDaoMixin
from activitytracker.db.models import DailyVideoSummary
from activitytracker.object.classes import CompletedVideoSession, VideoSession
from activitytracker.object.video_classes import YouTubeInfo

# from activitytracker.object.classes import VideoInfo  # TODO?
from activitytracker.tz_handling.dao_objects import FindTodaysEntryConverter
from activitytracker.tz_handling.time_formatting import (
    attach_tz_to_all,
    attach_tz_to_obj,
    get_start_of_day_from_datetime,
    get_start_of_day_from_ult,
)
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.const import SECONDS_PER_HOUR
from activitytracker.util.errors import ImpossibleToGetHereError, NegativeTimeError
from activitytracker.util.time_wrappers import UserLocalTime

# TODO: I think I do want all Pokemon grouped under Pokemon.
# Even better would be [Show] - [Series].
# I don't care about the particular episode.


class VideoSummaryDao(SummaryDaoMixin, UtilityDaoMixin):
    def __init__(self, video_logging_dao, reg_session: sessionmaker):
        self.video_logging_dao = video_logging_dao
        self.debug = False
        self.regular_session = reg_session
        self.logger = ConsoleLogger()
        self.model = DailyVideoSummary

    def start_session(self, video_session: VideoSession):
        """Creating the initial session for the summary

        Remember that Video is double counted on purpose!
        """
        self._create(video_session, video_session.start_time.dt)

    def _create(self, session: VideoSession, start_time: datetime):
        # self.logger.log_white("[debug] creating session: " + session.media_name
        today_start = get_start_of_day_from_datetime(start_time)

        channel_name = (
            session.video_info.channel_name
            if isinstance(session.video_info, YouTubeInfo)
            else None
        )

        new_entry = DailyVideoSummary(
            media_id=session.video_info.video_id,
            media_name=session.media_title,
            channel_name=channel_name,
            platform=session.video_info.get_platform_title(),
            # TODO: If YouTube, insert the channel name.
            # If Netflix, insert the movie name or series title.
            # If VLC, insert the movie name or series title.
            hours_spent=0,
            gathering_date=today_start,
            gathering_date_local=today_start.replace(tzinfo=None),
        )
        self.add_new_item(new_entry)

    def find_netflix_media_by_id(self, media_id: str):
        # TODO: Find entries more recent than three months. Because Netflix IDs change
        query = select(self.model).where(
            self.model.media_id == media_id and self.model.platform == "Netflix"
        )
        return self.execute_and_read_one_or_none(query)

    def find_todays_entry_for_media(
        self, video_session: VideoSession
    ) -> DailyVideoSummary | None:
        """Find by exe_path"""
        initializer = FindTodaysEntryConverter(video_session.start_time)

        query = self.create_find_all_from_day_query(
            video_session.media_title,
            initializer.start_of_day_with_tz,
            initializer.end_of_day_with_tz,
        )

        return self._execute_read_with_restored_tz(query, video_session.start_time)

    def create_find_all_from_day_query(self, media_title, start_of_day, end_of_day):
        # Use LTZ
        return select(DailyVideoSummary).where(
            DailyVideoSummary.media_name == media_title,
            DailyVideoSummary.gathering_date >= start_of_day,
            DailyVideoSummary.gathering_date < end_of_day,
        )

    def read_past_week(self, right_now: UserLocalTime) -> List[DailyVideoSummary]:
        # +1 because weekday() counts from Monday=0
        return self.do_read_past_week(right_now)  # type: ignore

    def read_day(self, day: UserLocalTime) -> List[DailyVideoSummary]:
        """Read all entries for the given day."""
        return self.do_read_day(day)  # type: ignore

    def read_all(self) -> List[DailyVideoSummary]:
        """Read all entries."""
        query = select(DailyVideoSummary)
        return self.execute_and_return_all(query)

    # Updates section

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

    def push_window_ahead_ten_sec(self, video_session: VideoSession):
        """
        Finds the given session and adds ten sec to its end_time

        NOTE: This only ever happens after start_session
        """
        if video_session is None:
            raise ValueError("Session should not be None")

        today_start = get_start_of_day_from_datetime(video_session.start_time.dt)
        query = self.select_where_time_equals_for_session(
            today_start, video_session.media_title
        )

        self.execute_window_push(
            query, video_session.media_title, video_session.start_time.dt
        )

    def select_where_time_equals_for_session(self, some_time, media_title):
        return select(DailyVideoSummary).where(
            DailyVideoSummary.media_name == media_title,
            DailyVideoSummary.gathering_date.op("=")(some_time),
        )

    def add_used_time(self, session: VideoSession, duration_in_sec: int):
        """
        When a session is concluded, it was concluded partway thru the 10 sec window

        9 times out of 10. So we add  the used  duration from its hours_spent.
        """
        self.add_partial_window(
            session, duration_in_sec, DailyVideoSummary.media_name == session.media_title
        )

    async def shutdown(self):
        """Closes the open session without opening a new one"""

        pass

    def close(self):
        if hasattr(self, "_current_session") and self._current_session is not None:
            self._current_session.close()
            self._current_session = None
