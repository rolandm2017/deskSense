
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker


from datetime import timedelta, datetime

from surveillance.src.db.dao.base_dao import BaseQueueingDao
from surveillance.src.db.models import TypingSession
from surveillance.src.object.classes import KeyboardAggregate
from surveillance.src.object.dto import TypingSessionDto
from surveillance.src.util.console_logger import ConsoleLogger
from surveillance.src.util.time_wrappers import UserLocalTime


def get_rid_of_ms(time):
    return str(time).split(".")[0]


class KeyboardDao(BaseQueueingDao):
    def __init__(self, async_session_maker: async_sessionmaker, batch_size=100, flush_interval=1):
        super().__init__(async_session_maker=async_session_maker,
                         batch_size=batch_size, flush_interval=flush_interval, dao_name="Keyboard")

        self.logger = ConsoleLogger()

    async def create(self, session: KeyboardAggregate):
        # FIXME: after 1 sec of no typing, session should "just conclude"
        # self.logger.log_green("[LOG] Keyboard session")
        # event time should be just month :: date :: HH:MM:SS
        new_typing_session_entry = TypingSession(
            start_time=session.start_time.get_dt_for_db(), end_time=session.end_time.get_dt_for_db())
        # self.logger.log_blue("[LOG] Keyboard event: " + str(session))
        await self.queue_item(new_typing_session_entry)

    async def create_without_queue(self, session: KeyboardAggregate):
        print("adding keystrokes to db ", str(session))
        new_session = TypingSession(
            start_time=session.start_time.get_dt_for_db(),
            end_time=session.end_time.get_dt_for_db()
        )

        # Create a new session from the session_maker
        async with self.async_session_maker() as db_session:
            # Begin a transaction
            async with db_session.begin():
                # Add the new session to the database
                db_session.add(new_session)
                # The commit is handled by the context manager when exiting the begin() block

            # Refresh to get any database-generated values (like IDs)
            await db_session.refresh(new_session)

        return new_session

    async def read_by_id(self, keystroke_id: int):
        """
        Read Keystroke entries. 
        """
        async with self.async_session_maker() as db_session:
            result = await db_session.get(TypingSession, keystroke_id)
            return result

    async def read_all(self):
        """Return all keystrokes."""
        query = select(TypingSession)
        all_results = await self.exec_and_return_all(query)

        dtos = self.package_dtos(all_results)

        return dtos

    def package_dtos(self, typing_sessions):
        return [TypingSessionDto(
            x.id, x.start_time, x.end_time) for x in typing_sessions]
        # return [TypingSessionDto(
        #     x[0].id, x[0].start_time, x[0].end_time) for x in typing_sessions]

    async def read_past_24h_events(self, right_now: UserLocalTime):
        """
        Read typing sessions from the past 24 hours, grouped into 5-minute intervals.
        Returns the count of sessions per interval.
        """
        try:
            twenty_four_hours_ago = right_now.dt - timedelta(hours=24)

            query = self.get_prev_24_hours_query(twenty_four_hours_ago)

            all_results = await self.exec_and_return_all(query)

            dtos = self.package_dtos(all_results)

            return dtos
        except Exception as e:
            print(e)
            raise RuntimeError("Failed to read typing sessions") from e

    def get_prev_24_hours_query(self, twenty_four_hours_ago):
        return select(TypingSession).where(
            TypingSession.start_time >= twenty_four_hours_ago
        ).order_by(TypingSession.start_time.desc())

    async def exec_and_return_all(self, query):
        async with self.async_session_maker() as session:
            result = await session.execute(query)
            result = result.all()
            return result

    async def delete(self, id: int):
        """Delete an entry by ID"""
        async with self.async_session_maker() as session:
            entry = await session.get(TypingSession, id)
            if entry:
                await session.delete(entry)
                await session.commit()
            return entry
