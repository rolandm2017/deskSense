# tiny_services.py
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
from activitytracker.object.pydantic_dto import UtcDtTabChange
from activitytracker.object.video_classes import NetflixInfo, YouTubeInfo
from activitytracker.tz_handling.time_formatting import convert_to_timezone
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.time_wrappers import UserLocalTime


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
