from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from datetime import timedelta, datetime

from activitytracker.db.dao.base_dao import BaseQueueingDao
# TODO: Replace with AsyncUtilityDaoMixin
from activitytracker.db.dao.utility_dao_mixin import AsyncUtilityDaoMixin

from activitytracker.db.models import MouseMove
from activitytracker.object.dto import MouseMoveDto
from activitytracker.object.classes import MouseMoveWindow
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.time_wrappers import UserLocalTime


def get_rid_of_ms(time):
    return str(time).split(".")[0]


class MouseDao(AsyncUtilityDaoMixin, BaseQueueingDao):
    def __init__(self, async_session_maker: async_sessionmaker, batch_size=100, flush_interval=1):
        super().__init__(async_session_maker=async_session_maker,
                         batch_size=batch_size, flush_interval=flush_interval, dao_name="Mouse")

        self.logger = ConsoleLogger()

    async def create_from_window(self, window: MouseMoveWindow):
        mouse_move = MouseMove(
            start_time=window.start_time.get_dt_for_db(), end_time=window.end_time.get_dt_for_db())
        await self.queue_item(mouse_move, MouseMove, "create_from_window")

    async def create_without_queue(self, start_time: UserLocalTime, end_time: UserLocalTime):
        new_mouse_move = MouseMove(
            start_time=start_time.dt,
            end_time=end_time.dt
        )

        async with self.async_session_maker() as db_session:
            async with db_session.begin():
                db_session.add(new_mouse_move)

            await db_session.refresh(new_mouse_move)

        return new_mouse_move

    async def read_all(self):
        """Read MouseMove entries."""
        query = select(MouseMove)

        return await self.execute_and_return_all_rows(query)

    async def read_by_id(self, mouse_move_id: int):
        async with self.async_session_maker() as session:
            return await session.get(MouseMove, mouse_move_id)

    async def read_past_24h_events(self, right_now: UserLocalTime):
        """
        Read mouse movement events that ended within the past 24 hours.
        Returns all movements ordered by their end time.
        """
        query = self.get_prev_24_hours_query(right_now.dt - timedelta(days=1))

        return await self.execute_and_return_all_rows(query)

    def get_prev_24_hours_query(self, twenty_four_hours_ago):
        return select(MouseMove).where(
            MouseMove.start_time >= twenty_four_hours_ago
        ).order_by(MouseMove.start_time.desc())

    async def delete(self, id: int):
        """Delete an entry by ID"""
        async with self.async_session_maker() as session:
            entry = await session.get(MouseMove, id)
            if entry:
                await session.delete(entry)
                await session.commit()
            return entry
