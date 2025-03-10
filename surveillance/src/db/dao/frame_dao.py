
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker


from datetime import datetime, timedelta

from .base_dao import BaseQueueingDao
from ..models import Frame, Video
from ...object.pydantic_dto import FrameCreateEvent
from ...util.console_logger import ConsoleLogger


class FrameDto:
    # Making IDE errors be quiet while I ignore this
    def __init__(self, id, start_time, end_time) -> None:
        self.id: int = id
        self.start_time: datetime = start_time
        self.end_time: datetime = end_time


class FrameDao(BaseQueueingDao):
    def __init__(self, session_maker: async_sessionmaker, batch_size=100, flush_interval=5):
        super().__init__(session_maker=session_maker,
                         batch_size=batch_size, flush_interval=flush_interval)

        self.logger = ConsoleLogger()

    async def create(self, frame: FrameCreateEvent):
        new_frame = Frame(
            video_id=frame.video_id,
            created_at=frame.created_at,
            frame_number=frame.frame_number
        )
        await self.queue_item(new_frame)

    async def read_by_id(self, frame_id: int):
        """Read Frame entries."""
        async with self.session_maker() as session:
            return await session.get(Frame, frame_id)

    async def read_all(self):
        """Return all frames."""
        async with self.session_maker() as session:
            result = await session.execute(select(Frame))
            result = result.all()
            dtos = [FrameDto(
                x[0].id, x[0].start_time, x[0].end_time) for x in result]

            return dtos

    async def read_past_24h_events(self, right_now: datetime):
        """Read typing sessions from the past 24 hours, grouped into 5-minute intervals.
        Returns the count of sessions per interval."""
        try:
            twenty_four_hours_ago = right_now - timedelta(hours=24)

            query = select(Frame).where(
                Frame.start_time >= twenty_four_hours_ago
            ).order_by(Frame.start_time.desc())

            async with self.session_maker() as session:
                result = await session.execute(query)
                rows = result.all()

                if not rows:  # Handle no results
                    return []

                dtos = [
                    FrameDto(x[0].id, x[0].start_time, x[0].end_time)
                    for x in rows
                ]
                return dtos
        except Exception as e:
            raise RuntimeError("Failed to read typing sessions") from e

    async def delete(self, id: int):
        """Delete an entry by ID"""
        async with self.session_maker() as session:
            entry = await session.get(Frame, id)
            if entry:
                await session.delete(entry)
                await session.commit()
            return entry
