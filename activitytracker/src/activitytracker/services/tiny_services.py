# services.py
from fastapi import Depends

import pytz
from datetime import date, datetime, time

from typing import List, cast

from activitytracker.config.definitions import local_time_zone, productive_sites
from activitytracker.db.dao.queuing.keyboard_dao import KeyboardDao
from activitytracker.db.dao.queuing.mouse_dao import MouseDao
from activitytracker.db.models import MouseMove
from activitytracker.object.classes import (
    PlayerStateChangeEventWithLtz,
    TabChangeEventWithLtz,
)
from activitytracker.object.dto import TypingSessionDto
from activitytracker.object.pydantic_dto import (
    NetflixPlayerChange,
    NetflixTabChange,
    UtcDtTabChange,
    YouTubePlayerChange,
    YouTubeTabChange,
)
from activitytracker.object.video_classes import NetflixInfo, YouTubeInfo
from activitytracker.tz_handling.time_formatting import convert_to_timezone
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.time_wrappers import UserLocalTime


class YouTubeTimezoneService:
    def __init__(self, parent_service):
        self.parent_service = parent_service

    def convert_tz_for_tab_change(self, tab_event: YouTubeTabChange, new_tz: str):
        youtube_info = YouTubeInfo(tab_event.channel, tab_event.playerState)
        return self._make_tab_change_event_with_youtube_info(tab_event, youtube_info, new_tz)

    def _make_tab_change_event_with_youtube_info(
        self, tab_event, youtube_info: YouTubeInfo, new_tz: str
    ):
        new_datetime_with_tz: datetime = convert_to_timezone(tab_event.startTime, new_tz)
        tab_change_with_time_zone = TabChangeEventWithLtz(
            tab_event.tabTitle,
            tab_event.url,
            UserLocalTime(new_datetime_with_tz),
            youtube_info,
        )
        return tab_change_with_time_zone

    def convert_tz_for_state_change(self, tab_event: YouTubePlayerChange, new_tz: str):
        youtube_info = YouTubeInfo(tab_event.channel, tab_event.playerState)
        return self._make_player_state_change_event(tab_event, youtube_info, new_tz)

    def _make_player_state_change_event(
        self, player_event: YouTubePlayerChange, youtube_info: YouTubeInfo, new_tz
    ):
        # FIXME: Need to make use of new_tz on the eventTime field
        new_datetime_with_tz: datetime = convert_to_timezone(player_event.eventTime, new_tz)

        state_change_event = PlayerStateChangeEventWithLtz(
            player_event.tabTitle,
            UserLocalTime(new_datetime_with_tz),
            youtube_info,
        )
        return state_change_event


class NetflixTimezoneService:
    def __init__(self, parent_service):
        self.parent_service = parent_service

    def convert_tz_for_tab_change(self, tab_event: NetflixTabChange, new_tz: str):
        netflix_info = NetflixInfo(tab_event.videoId, "paused")
        return self._make_tab_change_event_with_netflix_info(tab_event, netflix_info, new_tz)

    def _make_tab_change_event_with_netflix_info(
        self, tab_event: NetflixTabChange, netflix_info: NetflixInfo, new_tz: str
    ):
        new_datetime_with_tz: datetime = convert_to_timezone(tab_event.startTime, new_tz)
        tab_change_with_time_zone = TabChangeEventWithLtz(
            tab_event.tabTitle,
            tab_event.url,
            UserLocalTime(new_datetime_with_tz),
            netflix_info,
        )
        return tab_change_with_time_zone

    def convert_tz_for_state_change(self, tab_event: NetflixPlayerChange, new_tz: str):
        netflix_info = NetflixInfo(tab_event.videoId, tab_event.playerState)
        return self._make_player_state_change_event(tab_event, netflix_info, new_tz)

    def _make_player_state_change_event(
        self, player_event: NetflixPlayerChange, netflix_info: NetflixInfo, new_tz
    ):
        # FIXME: Need to make use of new_tz on the eventTime field
        new_datetime_with_tz: datetime = convert_to_timezone(player_event.eventTime, new_tz)

        state_change_event = PlayerStateChangeEventWithLtz(
            player_event.showName,
            UserLocalTime(new_datetime_with_tz),
            netflix_info,
        )
        return state_change_event


class TimezoneService:
    def __init__(self):
        self.youtube = YouTubeTimezoneService(self)
        self.netflix = NetflixTimezoneService(self)

    def get_tz_for_user(self, user_id):
        # TODO: In the future, read from a cache of recently active users.
        # TODO: If not in cache, read from the db.
        return local_time_zone

    def make_week_of_ult(self, week_of) -> UserLocalTime:
        if not isinstance(week_of, date):
            raise ValueError(
                f"Week of was not a date, it was: {type(week_of)}, value: {week_of}"
            )
        user_tz_str = self.get_tz_for_user(1)
        user_tz = pytz.timezone(user_tz_str)
        # Convert date to datetime with time at 00:00:00 and attach user timezone
        week_of_as_dt = user_tz.localize(datetime.combine(week_of, time(0, 0, 0)))
        as_ult = UserLocalTime(week_of_as_dt)
        return as_ult

    def convert_into_user_timezone_ult(self, day: datetime) -> UserLocalTime:
        user_tz_str = self.get_tz_for_user(1)
        user_tz = pytz.timezone(user_tz_str)
        # Convert date to datetime with time at 00:00:00 and attach user timezone
        week_of_as_dt = user_tz.localize(day)
        as_ult = UserLocalTime(week_of_as_dt)
        return as_ult

    def localize_to_user_tz(self, dt):
        user_tz_str = self.get_tz_for_user(1)
        user_tz = pytz.timezone(user_tz_str)
        return user_tz.localize(dt)

    def convert_tab_change_timezone(
        self, tab_change_event: UtcDtTabChange, new_tz: str
    ) -> TabChangeEventWithLtz:
        new_datetime_with_tz: datetime = convert_to_timezone(
            tab_change_event.startTime, new_tz
        )
        tab_change_with_time_zone = TabChangeEventWithLtz(
            tab_change_event.tabTitle,
            tab_change_event.url,
            UserLocalTime(new_datetime_with_tz),
            None,
        )
        return tab_change_with_time_zone


class CaptureSessionService:
    def __init__(self):
        pass

    def get_capture_start(self):
        return datetime(2025, 2, 2, 2, 2, 2)


class KeyboardService:
    def __init__(self, clock, dao: KeyboardDao = Depends()):
        self.clock = clock
        self.dao = dao

    async def get_past_days_events(self) -> List[TypingSessionDto]:
        events = await self.dao.read_past_24h_events(self.clock.now())
        return events

    async def get_all_events(self) -> List[TypingSessionDto]:
        return await self.dao.read_all()


class MouseService:
    def __init__(self, clock, dao: MouseDao = Depends()):
        self.clock = clock
        self.dao = dao

    async def get_past_days_events(self) -> List[MouseMove]:
        events = await self.dao.read_past_24h_events(self.clock.now())
        return events

    async def get_all_events(self) -> List[MouseMove]:
        return await self.dao.read_all()
