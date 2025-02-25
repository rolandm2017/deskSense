
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker


from datetime import timedelta

from .base_dao import BaseQueueingDao
from ..models import TypingSession
from ...object.classes import KeyboardAggregate
from ...object.dto import TypingSessionDto
from ...util.console_logger import ConsoleLogger


def get_rid_of_ms(time):
    return str(time).split(".")[0]


class KeyboardDao(BaseQueueingDao):
    def __init__(self, clock, session_maker: async_sessionmaker, batch_size=100, flush_interval=5):
        super().__init__(session_maker=session_maker,
                         batch_size=batch_size, flush_interval=flush_interval)

        self.system_clock = clock
        self.logger = ConsoleLogger()

    async def create(self, session: KeyboardAggregate):
        # FIXME: after 1 sec of no typing, session should "just conclude"
        # self.logger.log_green("[LOG] Keyboard session")
        # event time should be just month :: date :: HH:MM:SS
        new_typing_session_entry = TypingSession(
            start_time=session.session_start_time, end_time=session.session_end_time)
        # self.logger.log_blue("[LOG] Keyboard event: " + str(session))
        await self.queue_item(new_typing_session_entry)

    async def create_without_queue(self, session: KeyboardAggregate):  # TODO: Remove
        print("adding keystroke ", str(session))
        new_session = TypingSession(
            start_time=session.session_start_time,
            end_time=session.session_end_time
        )

        self.db.add(new_session)  # FIXME: this won't work w/ sessions
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

        async with self.session_maker() as session:
            result = await session.execute(select(TypingSession))
            result = result.all()
            dtos = [TypingSessionDto(
                x[0].id, x[0].start_time, x[0].end_time) for x in result]

            return dtos

    async def read_past_24h_events(self):
        """
        Read typing sessions from the past 24 hours, grouped into 5-minute intervals.
        Returns the count of sessions per interval.
        """
        try:
            twenty_four_hours_ago = self.system_clock.now() - timedelta(hours=24)

            query = select(TypingSession).where(
                TypingSession.start_time >= twenty_four_hours_ago
            ).order_by(TypingSession.start_time.desc())

            async with self.session_maker() as session:
                result = await session.execute(query)
                rows = result.all()

                if not rows:  # Handle no results
                    return []

                dtos = [
                    TypingSessionDto(x[0].id, x[0].start_time, x[0].end_time)
                    for x in rows
                ]
                return dtos
        except Exception as e:
            print(f"Error reading events: {e}")
            raise RuntimeError("Failed to read typing sessions") from e

    async def delete(self, id: int):
        """Delete an entry by ID"""
        async with self.session_maker() as session:
            entry = await session.get(TypingSession, id)
            if entry:
                await session.delete(entry)
                await session.commit()
            return entry
