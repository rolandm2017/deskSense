
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from asyncio import Queue
import asyncio

from datetime import datetime, timedelta

from .base_dao import BaseQueueingDao
from ..models import TypingSession
from ..database import AsyncSession, get_db
from ...object.classes import KeyboardAggregate
from ...object.dto import TypingSessionDto
from ...console_logger import ConsoleLogger


def get_rid_of_ms(time):
    return str(time).split(".")[0]


class KeyboardDao(BaseQueueingDao):
    def __init__(self, db: AsyncSession, batch_size=100, flush_interval=5):
        super().__init__(db, batch_size, flush_interval)

        self.logger = ConsoleLogger()

    async def create(self, session: KeyboardAggregate):
        # event time should be just month :: date :: HH:MM:SS
        self.logger.log_blue("[LOG] Keyboard event: " + str(session))
        self.queue_item(session)

    async def create_without_queue(self, session: KeyboardAggregate):
        print("adding keystroke ", str(session))
        new_session = TypingSession(
            start_time=session.session_start_time,
            end_time=session.session_end_time
        )

        self.db.add(new_session)
        await self.db.commit()
        await self.db.refresh(new_session)
        return new_session

    async def read(self, keystroke_id: int = None):
        """
        Read Keystroke entries. If keystroke_id is provided, return specific keystroke,
        otherwise return all keystrokes.
        """
        if keystroke_id:
            return await self.db.get(TypingSession, keystroke_id)

        result = await self.db.execute(select(TypingSession))
        result = result.all()
        # print(len(result), type(result[0]), result[0], "53ru")
        # print(result[0], isinstance(result[0][0], TypingSession), '60ru')
        # print([type(x)[0].__name__ for x in result], '61ru')

        assert all(isinstance(r[0], TypingSession)
                   for r in result)  # consider disabling for performance

        dtos = [TypingSessionDto(
            x[0].id, x[0].start_time, x[0].end_time) for x in result]

        return dtos

    async def read_past_24h_events(self):
        """
        Read typing sessions from the past 24 hours, grouped into 5-minute intervals.
        Returns the count of sessions per interval.
        """
        # Round start_time to 5-minute intervals for grouping
        timestamp_interval = func.date_trunc('hour', TypingSession.start_time) + \
            func.floor(func.date_part('minute', TypingSession.start_time) / 5) * \
            timedelta(minutes=5)

        twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

        query = select(TypingSession).where(
            TypingSession.start_time >= twenty_four_hours_ago
        ).order_by(TypingSession.start_time.desc())

        result = await self.db.execute(query)
        result = result.all()

        assert all(isinstance(r[0], TypingSession)
                   for r in result)  # consider disabling for performance

        dtos = [TypingSessionDto(
            x[0].id, x[0].start_time, x[0].end_time) for x in result]

        return dtos

    async def delete(self, keystroke_id: int):
        """Delete a Keystroke entry by ID"""
        keystroke = await self.db.get(TypingSession, keystroke_id)
        if keystroke:
            await self.db.delete(keystroke)
            await self.db.commit()
        return keystroke
