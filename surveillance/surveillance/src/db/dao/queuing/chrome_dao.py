from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from datetime import datetime, timedelta

from surveillance.src.base_dao import BaseQueueingDao
from surveillance.src.models import ChromeTab
from surveillance.src.util.console_logger import ConsoleLogger
from surveillance.src.object.classes import ChromeSessionData
from surveillance.src.config.definitions import max_content_len


class ChromeDao(BaseQueueingDao):
    def __init__(self, async_session_maker: async_sessionmaker, batch_size=100, flush_interval=1):
        super().__init__(async_session_maker=async_session_maker,
                         batch_size=batch_size, flush_interval=flush_interval, dao_name="ChromeDao")
        self.logger = ConsoleLogger()

    async def create(self, session: ChromeSessionData):
        # Truncate detail because the database col is VARCHAR(140)
        truncated_for_db_col = session.detail[:max_content_len] if len(
            session.detail) > max_content_len else session.detail

        assert isinstance(session.start_time,
                          datetime), "Start time wasn't set in a Chrome session"
        assert isinstance(session.end_time,
                          datetime), "End time wasn't set in a Chrome session"
        chrome_deliverable = ChromeTab(
            url=session.domain,
            tab_title=truncated_for_db_col,
            start_time=session.start_time,
            end_time=session.end_time,
            productive=session.productive
        )
        await self.queue_item(chrome_deliverable, "create")

    async def read_all(self):
        async with self.session_maker() as session:
            result = await session.execute(select(ChromeTab))
            return result.scalars().all()

    async def read_past_24h_events(self, right_now: datetime):
        """
        Read program activity events that ended within the past 24 hours.
        Returns all program sessions ordered by their end time.
        """
        query = select(ChromeTab).where(
            ChromeTab.created_at >= right_now - timedelta(days=1)
        ).order_by(ChromeTab.end_time.desc())
        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()

    async def delete(self):
        pass
