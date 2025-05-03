# services.py
from fastapi import Depends
from typing import List, cast

from datetime import datetime


from surveillance.src.object.pydantic_dto import UtcDtTabChange
from surveillance.surveillance.src.tz_handling.time_formatting import convert_to_timezone

from surveillance.src.db.dao.queuing.mouse_dao import MouseDao
from surveillance.src.db.dao.queuing.keyboard_dao import KeyboardDao
from surveillance.src.db.dao.queuing.video_dao import VideoDao
from surveillance.src.db.dao.direct.frame_dao import FrameDao
from surveillance.src.db.models import MouseMove
from surveillance.src.object.dto import TypingSessionDto
from surveillance.src.object.classes import TabChangeEventWithLtz


from surveillance.src.config.definitions import local_time_zone, productive_sites
from surveillance.src.util.console_logger import ConsoleLogger
from surveillance.src.util.time_wrappers import UserLocalTime


class TimezoneService:
    def __init__(self):
        pass

    def get_tz_for_user(self, user_id):
        # TODO: In the future, read from a cache of recently active users.
        # TODO: If not in cache, read from the db.
        return local_time_zone

    def convert_tab_change_timezone(self, tab_change_event: UtcDtTabChange, new_tz: str) -> TabChangeEventWithLtz:
        new_datetime_with_tz: datetime = convert_to_timezone(
            tab_change_event.startTime, new_tz)
        tab_change_with_time_zone = TabChangeEventWithLtz(
            tab_change_event.tabTitle, tab_change_event.url, UserLocalTime(new_datetime_with_tz))
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
