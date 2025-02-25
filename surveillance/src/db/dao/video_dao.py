
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker


from datetime import datetime, timedelta

from .base_dao import BaseQueueingDao
from ..models import Video
# from ...object.dto import VideoDto
from ...object.pydantic_dto import VideoCreateEvent
from ...util.console_logger import ConsoleLogger


class VideoDao(BaseQueueingDao):
    def __init__(self, clock, session_maker: async_sessionmaker, batch_size=100, flush_interval=5):
        super().__init__(session_maker=session_maker,
                         batch_size=batch_size, flush_interval=flush_interval)
        self.system_clock = clock
        self.logger = ConsoleLogger()

    async def create(self, create_event: VideoCreateEvent):
        new_video = Video(
            title=create_event.title, created_at=create_event.created_at)
        await self.queue_item(new_video)

    async def read_by_id(self, video_id: int):
        """
        Read Video entries. 
        """
        return await self.db.get(Video, video_id)

    async def read_all(self):
        """Return all videos."""

        async with self.session_maker() as session:
            result = await session.execute(select(Video))
            result = result.all()

            return result

    async def read_past_24h_events(self):
        """
        Read typing sessions from the past 24 hours, grouped into 5-minute intervals.
        Returns the count of sessions per interval.
        """
        try:
            twenty_four_hours_ago = self.system_clock.now() - timedelta(hours=24)

            query = select(Video).where(
                Video.start_time >= twenty_four_hours_ago
            ).order_by(Video.start_time.desc())

            async with self.session_maker() as session:
                result = await session.execute(query)
                rows = result.all()

                if not rows:  # Handle no results
                    return []

                return rows

        except Exception as e:
            print(f"Error reading events: {e}")
            raise RuntimeError("Failed to read typing sessions") from e

    async def delete(self, id: int):
        """Delete an entry by ID"""
        async with self.session_maker() as session:
            entry = await session.get(Video, id)
            if entry:
                await session.delete(entry)
                await session.commit()
            return entry
