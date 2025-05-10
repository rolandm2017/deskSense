# services.py
from fastapi import Depends

import pytz
from datetime import date, datetime, time

from typing import List, cast

from activitytracker.config.definitions import local_time_zone, productive_sites
from activitytracker.db.dao.queuing.keyboard_dao import KeyboardDao
from activitytracker.db.dao.queuing.mouse_dao import MouseDao
from activitytracker.db.models import MouseMove
from activitytracker.object.classes import TabChangeEventWithLtz
from activitytracker.object.dto import TypingSessionDto
from activitytracker.object.pydantic_dto import (
    UtcDtTabChange,
    YouTubePageEvent,
    YouTubePlayerChange,
    YouTubePlayerEvent,
    YouTubeTabChange,
)
from activitytracker.object.video_classes import YouTubeInfo
from activitytracker.tz_handling.time_formatting import convert_to_timezone
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.time_wrappers import UserLocalTime


class TimezoneService:
    def __init__(self):
        pass

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

    def convert_tz_for_youtube_tab_change(self, tab_event: YouTubeTabChange, new_tz: str):
        youtube_info = YouTubeInfo("paused", tab_event.pageEvent.channel)
        return self.make_tab_change_event_with_youtube_info(tab_event, youtube_info, new_tz)

    def convert_tz_for_youtube_state_change(
        self, tab_event: YouTubePlayerChange, new_tz: str
    ):
        youtube_info = YouTubeInfo(
            tab_event.playerEvent.playerState, tab_event.playerEvent.channel
        )
        return self.make_tab_change_event_with_youtube_info(tab_event, youtube_info, new_tz)

    def make_tab_change_event_with_youtube_info(
        self, tab_event, youtube_info: YouTubeInfo, tz
    ):
        new_datetime_with_tz: datetime = convert_to_timezone(tab_event.startTime, new_tz)
        tab_change_with_time_zone = TabChangeEventWithLtz(
            tab_event.tabTitle,
            tab_event.url,
            UserLocalTime(new_datetime_with_tz),
            youtube_info,
        )
        return tab_change_with_time_zone

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
