
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

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
        await self.queue_item(session, KeyboardAggregate)

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

    async def read_by_id(self, keystroke_id: int):
        """
        Read Keystroke entries. 
        """
        return await self.db.get(TypingSession, keystroke_id)

    async def read_all(self):
        """Return all keystrokes."""

        result = await self.db.execute(select(TypingSession))
        result = result.all()
        # assert all(isinstance(r[0], TypingSession)
        #    for r in result)  # consider disabling for performance
        print(result, '60ru')
        dtos = [TypingSessionDto(
            x[0].id, x[0].start_time, x[0].end_time) for x in result]

        return dtos

    async def read_past_24h_events(self):
        """
        Read typing sessions from the past 24 hours, grouped into 5-minute intervals.
        Returns the count of sessions per interval.
        """
        try:
            twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

            query = select(TypingSession).where(
                TypingSession.start_time >= twenty_four_hours_ago
            ).order_by(TypingSession.start_time.desc())

            result = await self.db.execute(query)
            rows = result.all()

            if not rows:  # Handle no results
                return []

            dtos = [
                TypingSessionDto(x[0].id, x[0].start_time, x[0].end_time)
                for x in rows
                if x[0] is not None  # Avoid invalid row structures
            ]
            return dtos
        except Exception as e:
            # Handle database exceptions gracefully
            print(f"Error reading events: {e}")
            raise RuntimeError("Failed to read typing sessions") from e

    async def delete(self, keystroke_id: int):
        """Delete a Keystroke entry by ID"""
        keystroke = await self.db.get(TypingSession, keystroke_id)
        if keystroke:
            await self.db.delete(keystroke)
            await self.db.commit()
        return keystroke
