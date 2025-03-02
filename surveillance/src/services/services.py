# services.py
from fastapi import Depends
from typing import List, cast

from ..db.dao.mouse_dao import MouseDao
from ..db.dao.keyboard_dao import KeyboardDao
from ..db.dao.program_dao import ProgramDao
from ..db.dao.video_dao import VideoDao
from ..db.dao.frame_dao import FrameDao
from ..db.models import TypingSession, Program, MouseMove
from ..object.dto import TypingSessionDto


from ..config.definitions import productive_sites
from ..util.console_logger import ConsoleLogger


class KeyboardService:
    def __init__(self, dao: KeyboardDao = Depends()):
        self.dao = dao

    async def get_past_days_events(self) -> List[TypingSessionDto]:
        events = await self.dao.read_past_24h_events()
        return events

    async def get_all_events(self) -> List[TypingSessionDto]:
        return await self.dao.read_all()


class MouseService:
    def __init__(self, dao: MouseDao = Depends()):
        self.dao = dao

    async def get_past_days_events(self) -> List[MouseMove]:
        events = await self.dao.read_past_24h_events()
        return events

    async def get_all_events(self) -> List[MouseMove]:
        return await self.dao.read_all()


class ProgramService:
    def __init__(self, dao: ProgramDao = Depends()):
        self.dao = dao

    async def get_past_days_events(self) -> List[Program]:
        events = await self.dao.read_past_24h_events()
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
