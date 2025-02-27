from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from datetime import datetime, timedelta

from .base_dao import BaseQueueingDao
from ..models import ChromeTab
from ...console_logger import ConsoleLogger
from ...object.classes import ChromeSessionData


class ChromeDao(BaseQueueingDao):
    def __init__(self, session_maker: async_sessionmaker, batch_size=100, flush_interval=5):
        super().__init__(session_maker, batch_size, flush_interval)
        self.logger = ConsoleLogger()

    async def create(self, session: ChromeSessionData):
        # Try without start_time end_time for now

        # Truncate detail because the database col is VARCHAR(255)
        varchar_limit = 255
        truncated_for_db_col = session.detail[:varchar_limit] if len(
            session.detail) > varchar_limit else session.detail

        chrome_deliverable = ChromeTab(
            url=session.domain, tab_title=truncated_for_db_col, productive=session.productive, tab_change_time=session.start_time)
        await self.queue_item(chrome_deliverable)

    async def read_all(self):
        async with self.session_maker() as session:
            result = await session.execute(select(ChromeTab))
            return result.scalars().all()

    # TODO: ChromeSession table - like DailySummary but for websites
    # TODO: If tab into chrome, get most recent active tab -- this is the current tab
    # TODO: If tab out of chrome, stop recording time into the active tab
    # TODO: For chrome tabs, if just_passing_through(): do not record time at all
    # TODO just_passing_thru() time should be like, < 600 ms.
    # TODO: Could also be, "if chrome_session.is_transient(): continue"
    # TODO: ProgramTracker concludes ChromeSession when tabbing off of Chrome.

    async def read_past_24h_events(self):
        """
        Read program activity events that ended within the past 24 hours.
        Returns all program sessions ordered by their end time.
        """
        query = select(ChromeTab).where(
            ChromeTab.created_at >= datetime.now() - timedelta(days=1)
        ).order_by(ChromeTab.end_time.desc())
        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()

    async def delete(self):
        pass
