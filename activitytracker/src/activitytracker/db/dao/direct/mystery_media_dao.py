from sqlalchemy import delete, func, select, text
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
from activitytracker.db.models import MysteryMedia
from activitytracker.object.classes import CompletedVideoSession, VideoSession
from activitytracker.object.video_classes import YouTubeInfo

# from activitytracker.object.classes import VideoInfo  # TODO?
from activitytracker.tz_handling.dao_objects import FindTodaysEntryConverter
from activitytracker.tz_handling.time_formatting import (
    attach_tz_to_all,
    attach_tz_to_obj,
    convert_to_utc,
    get_start_of_day_from_datetime,
    get_start_of_day_from_ult,
)
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.const import SECONDS_PER_HOUR
from activitytracker.util.errors import ImpossibleToGetHereError, NegativeTimeError
from activitytracker.util.time_wrappers import UserLocalTime

# If a Netflix "Unknown Watch Page" session was entered that way,
# put it in a cache saying, "Wait for this video ID's media title to appear."
# When the video's media title appears, go in and overwrite the Mystery Title
# in the db for that video ID.

# ALSO, if the media title is unknown, but the Netflix Page ID is already present
# in the db, from less than two weeks ago, you can just infer that it's the same media.

# OK SO where should we do this? I think in the ActivityRecorder is when it matters.

# HOW LONG to keep the video ID cached for? 72 hours without an identification?
# I think this means that, since User will turn his computer off every few hours,
# that it should get it's own Mystery Media Table.


class MysteryMediaDao(SummaryDaoMixin, UtilityDaoMixin):

    def __init__(self, reg_session: sessionmaker):
        self.debug = False
        self.regular_session = reg_session
        self.logger = ConsoleLogger()
        self.model = MysteryMedia

    def create(self, mystery_id: str, discovery_time: UserLocalTime):
        """
        Duplicate entries are
        """
        start_time_as_utc = convert_to_utc(discovery_time.dt)

        media = MysteryMedia(
            mystery_id=mystery_id,
            first_seen=start_time_as_utc,
            last_seen=start_time_as_utc,
            discovered_name=None,
            count=1,
        )
        self.add_new_item(media)

    def find_most_recent_fifty(self):
        """Find the 50 most recently seen MysteryMedia records"""
        query = select(self.model).order_by(self.model.last_seen.desc()).limit(50)
        return self.execute_and_return_all(query)

    def find_by_id(self, existing_row_id: str):
        query = select(self.model).where(self.model.mystery_id == existing_row_id)
        return self.execute_and_read_one_or_none(query)

    def delete_ancient_rows(self):
        """Deletes entries older than 7 days."""
        # TODO
        pass

    def delete_by_mystery_id(self, mystery_id: str):
        """
        Delete all MysteryMedia entries with the given mystery_id.

        Note: mystery_id corresponds to Netflix watch page URLs which may
        point to different media over time, so multiple entries may exist.

        Args:
            mystery_id: The mystery_id to delete all entries for

        Returns:
            int: Number of rows deleted
        """
        query = delete(self.model).where(self.model.mystery_id == mystery_id)
        result = self.execute_and_return_all(query)

        if self.debug:
            self.logger.log(f"Deleted {result} entries with mystery_id: {mystery_id}")

        return result
