from typing import Callable

from activitytracker.db.dao.direct.mystery_media_dao import MysteryMediaDao
from activitytracker.db.dao.direct.video_summary_dao import VideoSummaryDao
from activitytracker.db.dao.queuing.video_logs_dao import VideoLoggingDao
from activitytracker.object.classes import VideoSession


class NetflixMysteryTitleResolver:

    def __init__(
        self,
        mystery_media_dao: MysteryMediaDao,
        # From the Video Summary DAO
        find_netflix_media_by_id: Callable[[str], str | None],
        update_name_for_mystery_in_summary_table: Callable[[str, str], None],
        update_name_for_mystery_in_logging_table: Callable[[str, str], None],
    ) -> None:
        self.find_netflix_media_by_id = find_netflix_media_by_id
        self.update_name_for_mystery_in_summary_table = (
            update_name_for_mystery_in_summary_table
        )
        self.update_name_for_mystery_in_logging_table = (
            update_name_for_mystery_in_logging_table
        )
        self.mystery_media_dao = mystery_media_dao
        self.mystery_cache = NetflixMysteryCache()
        most_recent_50 = mystery_media_dao.find_most_recent_fifty()
        self.mystery_cache.init(most_recent_50)

    def recover_or_register_netflix_title(self, video_session: VideoSession) -> str:
        if video_session.media_title is None:
            found_title_or_unknown = self._discover_title_or_store_mystery(video_session)
            return found_title_or_unknown
        else:
            self._update_titles_if_mystery_title_found(video_session)
            # Put it's name, back into it's name
            return video_session.media_title

    def _discover_title_or_store_mystery(self, video_session: VideoSession) -> str:
        """
        For the case where the .media_title is None

        If it's a recently discovered media title*, get it's name! and proceed like it's normal

        If it isn't a recently discovered media title, put it in the mystery cache
        """
        # First, look in the Summary DAO for the ID of the media.
        video_id = video_session.video_info.video_id
        found_title = self.find_netflix_media_by_id(video_id)
        if found_title:
            return found_title
        else:
            # If it isn't there, put it in the Mystery Media table.
            wouldnt_be_a_duplicate = not self.mystery_cache.id_exists_in_mystery_cache(
                video_id
            )
            if wouldnt_be_a_duplicate:
                self.mystery_cache.store_mystery(video_id)
            self.mystery_media_dao.create(video_id, video_session.start_time)
            return "Unknown Media Title"

    def _update_titles_if_mystery_title_found(self, video_session: VideoSession):
        """For the case where the .media_title is not None"""
        id_is_in_mysteries = self.mystery_cache.id_exists_in_mystery_cache(
            video_session.video_info.video_id
        )
        if id_is_in_mysteries:
            self._forward_discovered_mystery_title(video_session)

    def _forward_discovered_mystery_title(self, video_session: VideoSession):
        """
        When a Netflix title comes in, and the video ID associated with the title
        is in the Mystery Media Cache, (1) update all entries for that Video ID
        with the newly discovered media title. (2) Take it out of the cache
        """
        # update summary DAO, logging DAOs for this ID with a name!
        self.update_name_for_mystery_in_summary_table(
            video_session.video_info.video_id, video_session.get_name()
        )
        self.update_name_for_mystery_in_logging_table(
            video_session.video_info.video_id, video_session.get_name()
        )
        self.mystery_cache.delete(video_session.video_info.video_id)
        self.mystery_media_dao.delete_by_mystery_id(video_session.video_info.video_id)


class NetflixMysteryCache:
    """An array of video IDs of recent mystery media (video IDs with unknown titles)"""

    def __init__(self) -> None:
        self.mysteries = []

    def init(self, top_fifty):
        self.mysteries = top_fifty

    def store_mystery(self, mystery_id):
        self.mysteries.append(mystery_id)

    def id_exists_in_mystery_cache(self, known_media_id):
        return known_media_id in self.mysteries

    def delete(self, discovered_id):
        self.mysteries.remove(discovered_id)


# SO what I want is,
# ONE: For a netflix media, where only the ID is known, for it to be super fast to look up if it's associated
# with a title.

# TWO: To be able to store a mystery ID in such a way that it can be looked for very fast.

# THREE: When a Netflix Mystery ID's true title is discovered, the DAOs update the
# title names from "Unknown Media Title" to the true title.


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
