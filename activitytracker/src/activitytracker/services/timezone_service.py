# tiny_services.py
import pytz
from datetime import date, datetime, time

from typing import List, Union, cast

from activitytracker.config.definitions import local_time_zone, productive_sites
from activitytracker.object.classes import (
    PlayerStateChangeEventWithLtz,
    TabChangeEventWithLtz,
)
from activitytracker.object.pydantic_dto import (
    EventType,
    Platform,
    UtcDtTabChange,
    VideoEvent,
)
from activitytracker.object.video_classes import NetflixInfo, YouTubeInfo
from activitytracker.tz_handling.time_formatting import convert_to_timezone
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.time_wrappers import UserLocalTime


class UnifiedVideoEventTimezoneService:
    def __init__(self):
        pass

    def convert_event_timezone(
        self, event: VideoEvent, user_tz: str
    ) -> Union[TabChangeEventWithLtz, PlayerStateChangeEventWithLtz]:
        """Convert any video event to the appropriate timezone-aware event"""

        # Convert the datetime to user timezone
        local_datetime = convert_to_timezone(event.event_time, user_tz)
        local_time = UserLocalTime(local_datetime)

        # Create platform-specific info object
        video_info = self._create_video_info(event)

        if event.event_type == EventType.TAB_CHANGE:
            return TabChangeEventWithLtz(
                tab_title=event.tab_title,
                url=event.url,
                start_time_with_tz=local_time,
                video_info=video_info,
            )
        else:  # PlayerStateEvent
            return PlayerStateChangeEventWithLtz(
                tab_title=event.tab_title,
                event_time_with_tz=local_time,
                video_info=video_info,
            )

    def _create_video_info(self, event: VideoEvent):
        """Create the appropriate video info object based on platform"""
        if event.platform == Platform.YOUTUBE:
            return YouTubeInfo(
                channel_name=event.channel or "Unknown",
                video_id=event.video_id,
                player_state=event.player_state,
            )
        else:  # Netflix
            return NetflixInfo(
                media_title=event.show_name or event.tab_title,
                video_id=event.video_id,
                player_state=event.player_state,
            )


class TimezoneService:
    def __init__(self):
        self.converter = UnifiedVideoEventTimezoneService()

    def convert_any_video_event(self, event: VideoEvent, user_id: int = 1):
        """Single method to convert any video event to timezone-aware format"""
        user_tz = self.get_tz_for_user(user_id)
        return self.converter.convert_event_timezone(event, user_tz)

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
