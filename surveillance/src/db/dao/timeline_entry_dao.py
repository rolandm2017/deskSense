# timeline_entry_dao.py
# TODO
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from asyncio import Queue
import asyncio
from datetime import datetime, timedelta

from .base_dao import BaseQueueingDao
from ..models import TimelineEntryObj
from ...object.dto import ProgramDto
from ...object.classes import KeyboardAggregate, MouseMoveWindow
from ...object.enums import ChartEventType
from ...console_logger import ConsoleLogger


class TimelineEntryDao(BaseQueueingDao):
    def __init__(self, db: AsyncSession, batch_size=100, flush_interval=5):
        super().__init__(db, batch_size, flush_interval)
        self.logger = ConsoleLogger()

    async def create_from_keyboard_aggregate(self, content: KeyboardAggregate):
        highest_id = await self.read_highest_id()
        # Fixed: was "mouse-" before
        client_facing_id = f"keyboard-{highest_id + 1}"
        group = ChartEventType.KEYBOARD
        content_text = f"Typing Session {highest_id + 1}"
        new_row = TimelineEntryObj(
            clientFacingId=client_facing_id,  # Fixed: match the model's camelCase
            group=group,
            content=content_text,
            start=content.session_start_time,
            end=content.session_end_time
        )
        await self.create(new_row)

    async def create_from_mouse_move_window(self, content: MouseMoveWindow):
        highest_id = await self.read_highest_id()
        client_facing_id = f"mouse-{highest_id + 1}"
        group = ChartEventType.MOUSE
        content_text = f"Mouse Event {highest_id + 1}"
        new_row = TimelineEntryObj(
            clientFacingId=client_facing_id,
            group=group,
            content=content_text,
            start=content.start_time,
            end=content.end_time
        )
        await self.create(new_row)

    async def create(self, new_row: TimelineEntryObj):
        await self.queue_item(new_row, TimelineEntryObj)

    async def read_highest_id(self):
        """Read the highest ID currently in the table"""
        query = select(func.max(TimelineEntryObj.id))
        result = await self.db.execute(query)
        max_id = result.scalar()
        return max_id or 0  # Return 0 if table is empty

    async def read_day(self, day: datetime, event_type: ChartEventType):
        """Read all entries for the given day"""
        start_of_day = datetime.combine(day.date(), datetime.min.time())
        end_of_day = start_of_day + timedelta(days=1)

        query = select(TimelineEntryObj).where(
            TimelineEntryObj.start >= start_of_day,
            TimelineEntryObj.start < end_of_day,
            TimelineEntryObj.group == event_type
        ).order_by(TimelineEntryObj.start)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def read_day_mice(self, day: datetime):
        return self.read_day(day, ChartEventType.MOUSE)

    async def read_day_keyboard(self, day: datetime):
        return self.read_day(day, ChartEventType.KEYBOARD)

    async def read_all(self):
        """Read all timeline entries"""
        result = await self.db.execute(select(TimelineEntryObj))
        return result.scalars().all()

    async def delete(self, id: int):
        """Delete an entry by ID"""
        entry = await self.db.get(TimelineEntryObj, id)
        if entry:
            await self.db.delete(entry)
            await self.db.commit()
        return entry
