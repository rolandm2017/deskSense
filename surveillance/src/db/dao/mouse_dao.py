from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

import datetime

from .base_dao import BaseQueueingDao

from ..models import MouseMove
from ...object.dto import MouseMoveDto
from ...trackers.mouse_tracker import MouseMoveWindow
from ...console_logger import ConsoleLogger


def get_rid_of_ms(time):
    return str(time).split(".")[0]


class MouseDao(BaseQueueingDao):
    def __init__(self, session_maker: async_sessionmaker, batch_size=100, flush_interval=5):
        super().__init__(session_maker, batch_size, flush_interval)
        self.logger = ConsoleLogger()

    async def create_from_start_end_times(self, start_time: datetime, end_time: datetime):
        mouse_move = MouseMove(start_time=start_time, end_time=end_time)

        if isinstance(mouse_move, MouseMoveWindow):
            raise ValueError("mouse move window found!")
        # FIXME: A "MouseMove" goes in, but the Queue receives a MouseMoveWindow!
        await self.queue_item(mouse_move, MouseMove)

    async def create_from_window(self, window: MouseMoveWindow):  # TODO: Remove
        # Create dict first, to avoid MouseMoveWindow "infesting" a MouseMove object.
        # See SHA 52d3c13c3150c5859243b909d47d609f5b2b8600 to experience the issue.
        mouse_move = MouseMove(
            start_time=window.start_time, end_time=window.end_time)
        # FIXME: A "MouseMove" goes in, but the Queue receives a MouseMoveWindow!
        await self.queue_item(mouse_move, MouseMove)

    async def create_without_queue(self, start_time: datetime, end_time: datetime):
        # print("creating mouse move event", start_time)
        new_mouse_move = MouseMove(
            start_time=start_time,
            end_time=end_time
        )

        self.db.add(new_mouse_move)   # FIXME: this won't work w/ sessions
        await self.db.commit()
        await self.db.refresh(new_mouse_move)
        return new_mouse_move

    async def read_all(self):
        """
        Read MouseMove entries.
        """
        async with self.session_maker() as session:
            result = await session.execute(select(MouseMove))
            # return await result.scalars().all()  # TODO: return Dtos
            # FIXME: Some tests think this needs to be 'awaited' but it doens't
            return result.scalars().all()  # TODO: return Dtos

    async def read_by_id(self, mouse_move_id: int):
        async with self.session_maker() as session:
            return await session.get(MouseMove, mouse_move_id)

    async def read_past_24h_events(self):
        """
        Read mouse movement events that ended within the past 24 hours.
        Returns all movements ordered by their end time.
        """
        query = select(MouseMove).where(
            MouseMove.end_time >= datetime.datetime.now() - datetime.timedelta(days=1)
        ).order_by(MouseMove.end_time.desc())

        async with self.session_maker() as session:
            result = await session.execute(query)
            # FIXME: Some tests think this needs to be 'awaited' but it doens't
            # return await result.scalars().all()  # TODO: return Dtos
            return result.scalars().all()  # TODO: return Dtos

    async def delete(self, id: int):
        """Delete an entry by ID"""
        async with self.session_maker() as session:
            entry = await session.get(MouseMove, id)
            if entry:
                await session.delete(entry)
                await session.commit()
            return entry
