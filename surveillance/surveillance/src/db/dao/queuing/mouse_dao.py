from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from datetime import timedelta, datetime

from surveillance.src.db.dao.base_dao import BaseQueueingDao

from surveillance.src.db.models import MouseMove
from surveillance.src.object.dto import MouseMoveDto
from surveillance.src.object.classes import MouseMoveWindow
from surveillance.src.util.console_logger import ConsoleLogger


def get_rid_of_ms(time):
    return str(time).split(".")[0]


class MouseDao(BaseQueueingDao):
    def __init__(self, async_session_maker: async_sessionmaker, batch_size=100, flush_interval=1):
        super().__init__(async_session_maker=async_session_maker,
                         batch_size=batch_size, flush_interval=flush_interval, dao_name="Mouse")

        self.logger = ConsoleLogger()

    async def create_from_start_end_times(self, start_time: datetime, end_time: datetime):
        mouse_move = MouseMove(start_time=start_time, end_time=end_time)
        if isinstance(mouse_move, MouseMoveWindow):
            raise ValueError("mouse move window found!")
        await self.queue_item(mouse_move, MouseMove, "create_from_start_end_times")

    async def create_from_window(self, window: MouseMoveWindow):
        # Create dict first, to avoid MouseMoveWindow "infesting" a MouseMove object.
        # See SHA 52d3c13c3150c5859243b909d47d609f5b2b8600 to experience the issue.
        # self.logger.log_green("[LOG] Mouse move")
        mouse_move = MouseMove(
            start_time=window.start_time, end_time=window.end_time)
        await self.queue_item(mouse_move, MouseMove, "create_from_window")

    async def create_without_queue(self, start_time: datetime, end_time: datetime):
        new_mouse_move = MouseMove(
            start_time=start_time,
            end_time=end_time
        )

        async with self.session_maker() as db_session:
            async with db_session.begin():
                db_session.add(new_mouse_move)

            await db_session.refresh(new_mouse_move)

        return new_mouse_move

    async def read_all(self):
        """Read MouseMove entries."""
        async with self.session_maker() as session:
            result = await session.execute(select(MouseMove))
            # return await result.scalars().all()
            # Some tests think this needs to be 'awaited' but it doens't
            return result.scalars().all()

    async def read_by_id(self, mouse_move_id: int):
        async with self.session_maker() as session:
            return await session.get(MouseMove, mouse_move_id)

    async def read_past_24h_events(self, right_now: datetime):
        """
        Read mouse movement events that ended within the past 24 hours.
        Returns all movements ordered by their end time.
        """
        query = select(MouseMove).where(
            MouseMove.end_time >= right_now - timedelta(days=1)
        ).order_by(MouseMove.end_time.desc())

        async with self.session_maker() as session:
            result = await session.execute(query)
            # Some tests think this needs to be 'awaited' but it doens't
            # return await result.scalars().all()
            return result.scalars().all()

    async def delete(self, id: int):
        """Delete an entry by ID"""
        async with self.session_maker() as session:
            entry = await session.get(MouseMove, id)
            if entry:
                await session.delete(entry)
                await session.commit()
            return entry
