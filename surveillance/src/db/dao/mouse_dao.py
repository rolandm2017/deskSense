from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import datetime
from copy import deepcopy

from .base_dao import BaseQueueingDao

from ..models import MouseMove
from ..database import AsyncSession
from ...object.dto import MouseMoveDto
from ...trackers.mouse_tracker import MouseMoveWindow
from ...console_logger import ConsoleLogger


def get_rid_of_ms(time):
    return str(time).split(".")[0]


class MouseDao(BaseQueueingDao):
    def __init__(self, db: AsyncSession, batch_size=100, flush_interval=5):
        super().__init__(db, batch_size, flush_interval)

        self.logger = ConsoleLogger()

    async def create_from_start_end_times(self, start_time: datetime, end_time: datetime):
        mouse_move = MouseMove(start_time=start_time, end_time=end_time)

        if isinstance(mouse_move, MouseMoveWindow):
            raise ValueError("mouse move window found!")
        self.logger.log_red("Queuing " + str(mouse_move) + ' 28ru')
        # FIXME: A "MouseMove" goes in, but the Queue receives a MouseMoveWindow!
        await self.queue_item(mouse_move, MouseMove)

    async def create_from_window(self, window: MouseMoveWindow):
        # Create dict first, to avoid MouseMoveWindow "infesting" a MouseMove object.
        # See SHA 52d3c13c3150c5859243b909d47d609f5b2b8600 to experience the issue.
        mouse_move = MouseMove(
            start_time=window.start_time, end_time=window.end_time)
        if isinstance(mouse_move, MouseMoveWindow):
            raise ValueError("mouse move window found")
        self.logger.log_red("Queuing " + str(mouse_move) + ' 36ru')
        # FIXME: A "MouseMove" goes in, but the Queue receives a MouseMoveWindow!
        await self.queue_item(mouse_move, MouseMove)

    async def create_without_queue(self, start_time: datetime, end_time: datetime):
        # print("creating mouse move event", start_time)
        new_mouse_move = MouseMove(
            start_time=start_time,
            end_time=end_time
        )

        self.db.add(new_mouse_move)
        await self.db.commit()
        await self.db.refresh(new_mouse_move)
        return new_mouse_move

    async def read(self, mouse_move_id: int = None):
        """
        Read MouseMove entries. If mouse_move_id is provided, return specific movement,
        otherwise return all movements.
        """
        if mouse_move_id:
            return await self.db.get(MouseMove, mouse_move_id)

        result = await self.db.execute(select(MouseMove))
        return result.scalars().all()  # TODO: return Dtos

    async def read_past_24h_events(self):
        """
        Read mouse movement events that ended within the past 24 hours.
        Returns all movements ordered by their end time.
        """
        query = select(MouseMove).where(
            MouseMove.end_time >= datetime.datetime.now() - datetime.timedelta(days=1)
        ).order_by(MouseMove.end_time.desc())

        result = await self.db.execute(query)
        return result.scalars().all()  # TODO: return Dtos

    async def delete(self, mouse_move_id: int):
        """Delete a MouseMove entry by ID"""
        mouse_move = await self.db.get(MouseMove, mouse_move_id)
        if mouse_move:
            await self.db.delete(mouse_move)
            await self.db.commit()
        return mouse_move
