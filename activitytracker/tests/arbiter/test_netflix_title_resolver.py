from unittest.mock import MagicMock, Mock

import pytz
from datetime import datetime

from activitytracker.arbiter.netflix_title_resolver import (
    NetflixMysteryCache,
    NetflixMysteryTitleResolver,
)
from activitytracker.db.dao.direct.mystery_media_dao import MysteryMediaDao
from activitytracker.object.classes import VideoSession
from activitytracker.object.video_classes import NetflixInfo
from activitytracker.util.time_wrappers import UserLocalTime

tokyo_tz_string = "Asia/Tokyo"
tokyo_tz = pytz.timezone(tokyo_tz_string)

tokyo_now = tokyo_tz.localize(datetime.now())

session_start_time = UserLocalTime(tokyo_now)


class TestNetflixMysteryTitleResolver:
    class TestIncomingMediaHasKnownTitle:
        def test_known_title_no_mystery(self, mock_regular_session_maker):
            """
            It's a known title. The title is not a mystery, so it's not in the cache.
            """
            netflix_info = NetflixInfo("Hilda", "23434", "playing")
            netflix_video_session = VideoSession(
                "Hilda", None, netflix_info, session_start_time, True
            )

            mystery_dao = MysteryMediaDao(mock_regular_session_maker)

            find_netflix_media_mock = Mock(return_value="Test Movie Title")
            update_summary_mock = Mock()
            update_logging_mock = Mock()

            resolver = NetflixMysteryTitleResolver(
                mystery_dao,
                find_netflix_media_mock,
                update_summary_mock,
                update_logging_mock,
            )

            id_exists_in_mystery_cache_spy = Mock(
                side_effect=resolver.mystery_cache.id_exists_in_mystery_cache
            )
            resolver.mystery_cache.id_exists_in_mystery_cache = (
                id_exists_in_mystery_cache_spy
            )

            updated_title = resolver.recover_or_register_netflix_title(netflix_video_session)

            # Because there's nothing to change, it's already known
            assert updated_title == netflix_video_session.media_title

            id_exists_in_mystery_cache_spy.assert_called_once_with(netflix_info.video_id)

        def test_known_title_for_mystery_id(self, mock_regular_session_maker):
            """
            The Video ID's title was a mystery when the title arrived.

            Hence tables with "Unknown Media Title" are overwritten with the right title.
            """
            netflix_info = NetflixInfo("Hilda", "23434", "playing")
            netflix_video_session = VideoSession(
                "Hilda", None, netflix_info, session_start_time, True
            )

            mystery_dao = MysteryMediaDao(mock_regular_session_maker)
            delete_by_id_spy = Mock(side_effect=mystery_dao.delete_by_mystery_id)
            mystery_dao.delete_by_mystery_id = delete_by_id_spy

            find_netflix_media_mock = Mock(return_value="Test Movie Title")
            update_summary_mock = Mock()
            update_logging_mock = Mock()

            resolver = NetflixMysteryTitleResolver(
                mystery_dao,
                find_netflix_media_mock,
                update_summary_mock,
                update_logging_mock,
            )

            resolver.mystery_cache.store_mystery(netflix_info.video_id)

            id_exists_in_mystery_cache_spy = Mock(
                side_effect=resolver.mystery_cache.id_exists_in_mystery_cache
            )
            resolver.mystery_cache.id_exists_in_mystery_cache = (
                id_exists_in_mystery_cache_spy
            )

            delete_spy = Mock(side_effect=resolver.mystery_cache.delete)
            resolver.mystery_cache.delete = delete_spy

            updated_title = resolver.recover_or_register_netflix_title(netflix_video_session)

            assert updated_title == netflix_video_session.media_title

            id_exists_in_mystery_cache_spy.assert_called_once_with(netflix_info.video_id)

            update_logging_mock.assert_called_once_with(netflix_info.video_id, "Hilda")
            update_summary_mock.assert_called_once_with(netflix_info.video_id, "Hilda")
            delete_spy.assert_called_once_with(netflix_info.video_id)
            delete_by_id_spy.assert_called_once_with(netflix_info.video_id)

    class TestIncomingMediaWithUnknownTitle:
        def test_unknown_title_id_not_yet_in_cache(self, mock_regular_session_maker):
            netflix_info = NetflixInfo(None, "23434", "playing")
            netflix_video_session = VideoSession(
                None, None, netflix_info, session_start_time, True
            )

            mystery_dao = MysteryMediaDao(mock_regular_session_maker)

            create_spy = Mock(side_effect=mystery_dao.create)
            mystery_dao.create = create_spy

            delete_by_id_spy = Mock(side_effect=mystery_dao.delete_by_mystery_id)
            mystery_dao.delete_by_mystery_id = delete_by_id_spy

            find_netflix_media_mock = Mock(return_value=None)
            update_summary_mock = Mock()
            update_logging_mock = Mock()

            resolver = NetflixMysteryTitleResolver(
                mystery_dao,
                find_netflix_media_mock,
                update_summary_mock,
                update_logging_mock,
            )

            update_for_title = resolver.recover_or_register_netflix_title(
                netflix_video_session
            )

            assert update_for_title == "Unknown Media Title"

            assert resolver.mystery_cache.id_exists_in_mystery_cache(netflix_info.video_id)
            create_spy.assert_called_once_with(
                netflix_info.video_id, netflix_video_session.start_time
            )

        def test_unknown_title_with_id_present_in_cache(self, mock_regular_session_maker):
            netflix_info = NetflixInfo(None, "23434", "playing")
            netflix_video_session = VideoSession(
                None, None, netflix_info, session_start_time, True
            )

            mystery_dao = MysteryMediaDao(mock_regular_session_maker)

            create_spy = Mock(side_effect=mystery_dao.create)
            mystery_dao.create = create_spy

            delete_by_id_spy = Mock(side_effect=mystery_dao.delete_by_mystery_id)
            mystery_dao.delete_by_mystery_id = delete_by_id_spy

            find_netflix_media_mock = Mock(return_value=None)
            update_summary_mock = Mock()
            update_logging_mock = Mock()

            resolver = NetflixMysteryTitleResolver(
                mystery_dao,
                find_netflix_media_mock,
                update_summary_mock,
                update_logging_mock,
            )
            # "ID present in cache"
            resolver.mystery_cache.store_mystery(netflix_info.video_id)

            store_mystery_spy = Mock(side_effect=resolver.mystery_cache.store_mystery)
            resolver.mystery_cache.store_mystery = store_mystery_spy

            update_for_title = resolver.recover_or_register_netflix_title(
                netflix_video_session
            )

            assert update_for_title == "Unknown Media Title"

            # It was already there, so don't re-add it
            store_mystery_spy.assert_not_called()

            create_spy.assert_called_once_with(
                netflix_info.video_id, netflix_video_session.start_time
            )


class TestMysteryCache:
    def test_init(self):
        cache = NetflixMysteryCache()

        init_ids = [1, 2, 3, 5]

        cache.init(init_ids)

        assert len(cache.mysteries) == 4
        assert cache.id_exists_in_mystery_cache(10) is False
        assert cache.id_exists_in_mystery_cache(1) is True
        assert cache.id_exists_in_mystery_cache(5) is True

    def test_store_mystery(self):
        cache = NetflixMysteryCache()

        cache.store_mystery(5)

        assert cache.mysteries[0] == 5

    def test_contains_mystery(self):
        cache = NetflixMysteryCache()

        cache.store_mystery(5)
        cache.store_mystery(10)
        cache.store_mystery(15)

        assert cache.id_exists_in_mystery_cache(5)
        assert cache.id_exists_in_mystery_cache(10)

    def test_delete(self):
        cache = NetflixMysteryCache()

        cache.store_mystery(5)
        cache.store_mystery(10)
        cache.store_mystery(15)

        assert cache.id_exists_in_mystery_cache(5)
        assert cache.id_exists_in_mystery_cache(10)

        cache.delete(5)

        assert cache.id_exists_in_mystery_cache(5) is False
