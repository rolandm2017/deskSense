
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker


from datetime import datetime, timedelta

from ..base_dao import BaseQueueingDao
from ...models import Video
# from ...object.dto import VideoDto
from ....object.pydantic_dto import VideoCreateEvent
from ....util.console_logger import ConsoleLogger


class VideoDao(BaseQueueingDao):
    def __init__(self, session_maker: async_sessionmaker, batch_size=100, flush_interval=1):
        super().__init__(session_maker=session_maker,
                         batch_size=batch_size, flush_interval=flush_interval, dao_name="Video")

        self.logger = ConsoleLogger()

    async def create(self, create_event: VideoCreateEvent):
        """
        Create a new video and return its ID.
        This method does not use queuing to ensure we can return the generated ID.
        """
        new_video = Video(
            title=create_event.title, created_at=create_event.created_at)

        # For immediate ID return, we need to commit directly instead of queuing
        async with self.session_maker() as session:
            session.add(new_video)
            await session.flush()  # This assigns the ID but doesn't commit yet
            video_id = new_video.id  # Get the generated ID
            await session.commit()  # Now commit the transaction

        return video_id

    async def create_queued(self, create_event: VideoCreateEvent):
        """
        Queue a video creation without returning ID.
        Use this method when you don't need the ID immediately.
        """
        new_video = Video(
            title=create_event.title, created_at=create_event.created_at)
        await self.queue_item(new_video)

    # async def create(self, create_event: VideoCreateEvent):
    #     new_video = Video(
    #         title=create_event.title, created_at=create_event.created_at)
    #     await self.queue_item(new_video)

    async def read_by_id(self, video_id: int):
        """
        Read Video entries. 
        """
        async with self.session_maker() as db_session:
            result = await db_session.get(Video, video_id)
            return result

    async def read_all(self):
        """Return all videos."""

        async with self.session_maker() as session:
            result = await session.execute(select(Video))
            result = result.all()

            return result

    async def read_past_24h_events(self, right_now: datetime):
        """
        Read typing sessions from the past 24 hours, grouped into 5-minute intervals.
        Returns the count of sessions per interval.
        """
        try:
            twenty_four_hours_ago = right_now - timedelta(hours=24)

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
