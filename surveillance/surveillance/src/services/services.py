# services.py
from fastapi import Depends
from typing import List, cast

from surveillance.src.object.dashboard_dto import MouseEventsPayload


from surveillance.src.facade.keyboard_facade import KeyboardFacadeCore

from surveillance.src.object.pydantic_dto import TabChangeEvent
from surveillance.src.util.time_formatting import convert_to_timezone

from surveillance.src.db.dao.queuing.mouse_dao import MouseDao
from surveillance.src.db.dao.queuing.keyboard_dao import KeyboardDao
from surveillance.src.db.dao.queuing.program_dao import ProgramDao
from surveillance.src.db.dao.queuing.video_dao import VideoDao
from surveillance.src.db.dao.direct.frame_dao import FrameDao
from surveillance.src.db.models import TypingSession, Program, MouseMove
from surveillance.src.object.dto import TypingSessionDto


from surveillance.src.config.definitions import local_time_zone, productive_sites
from surveillance.src.util.console_logger import ConsoleLogger


class TimezoneService:
    def __init__(self):
        pass

    def get_tz_for_user(self, user_id):
        # TODO: In the future, read from a cache of recently active users.
        # TODO: If not in cache, read from the db.
        return local_time_zone

    def convert_tab_change_timezone(self, tab_change_event: TabChangeEvent, new_tz: str):
        new_datetime_with_tz = convert_to_timezone(
            tab_change_event.startTime, new_tz)
        tab_change_event.startTime = new_datetime_with_tz
        return tab_change_event


# class TrackerService:
#     def __init__(self, keyboard_facade, mouse_facade) -> None:
#         # TODO: Make this singleton or at least all from the same place
#         self.keyboard_facade = keyboard_facade
#         self.mouse_facade = mouse_facade

#     def receive_keyboard_event(self, time):
#         self.keyboard_facade.receive_key(time)

#     def receive_mouse_events(self, payload: MouseEventsPayload):
#         self.mouse_facade.receive_payload(payload)


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


class ProgramService:
    def __init__(self, clock, dao: ProgramDao = Depends()):
        self.clock = clock
        self.dao = dao

    async def get_past_days_events(self) -> List[Program]:
        events = await self.dao.read_past_24h_events(self.clock.now())
        return events

    async def get_all_events(self) -> List[Program]:
        return await self.dao.read_all()


class VideoService:
    def __init__(self, video_dao: VideoDao, frame_dao: FrameDao):
        self.video_dao = video_dao
        self.frame_dao = frame_dao

    async def create_new_video(self, video_create_event) -> int:
        new_video_id = await self.video_dao.create(video_create_event)
        new_video_id = cast(int, new_video_id)
        return new_video_id

    async def add_frame_to_video(self, add_frame_event):
        return await self.frame_dao.create(add_frame_event)
