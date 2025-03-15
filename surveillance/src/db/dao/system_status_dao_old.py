from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select, desc, func

from datetime import datetime

from ...object.enums import SystemStatusType
from ...util.console_logger import ConsoleLogger
from ..models import SystemStatus

# A table that tracks the status of the computer.


class SystemStatusDao:
    """
    Does NOT use the queue because read/write here 
    should always always get priority, i.e.  no queue!
    """

    def __init__(self, session_maker: async_sessionmaker, batch_size=100, flush_interval=5):
        """ Exists mostly for debugging. """
        self.session_maker = session_maker
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.logger = ConsoleLogger()

    def accept_event_loop(self, loop):
        self.power_tracker_loop = loop

    async def create_status(self, status: SystemStatusType, now: datetime):
        print(f"[debug - create_status] {status}, type: {type(status)}")

        try:
            if status == SystemStatusType.STARTUP:
                latest_status = await self.read_latest_status()
                print("[info] Found status: ", latest_status)
                if latest_status == SystemStatusType.HOT_RELOAD_STARTED:
                    # It's not only a STARTUP, it's recovering from a hot reload.
                    status = SystemStatusType.HOT_RELOAD_RECOVERY

            print(f"Writing status to database: {status}")
            async with self.session_maker() as session:
                new_status = SystemStatus(
                    status=status,
                    created_at=now
                )
                session.add(new_status)
                await session.commit()
                print("Database commit successful")
                self.logger.log_white_multiple(
                    "[system status dao] recorded status change: ", status)
        except Exception as e:
            print(f"Error in create_status: {e}")
            import traceback
            traceback.print_exc()
            # Don't re-raise - this is critical shutdown code

    async def create_status_v1(self, status: SystemStatusType, now: datetime):
        print("[debug - create_status]", status)
        if status == SystemStatusType.STARTUP:
            latest_status = await self.read_latest_status()
            print("[info] Found status: ", latest_status)
            if latest_status == SystemStatusType.HOT_RELOAD_STARTED:
                # It's not only a STARTUP, it's recovering from a hot reload.
                status = SystemStatusType.HOT_RELOAD_RECOVERY
        async with self.session_maker() as session:
            new_status = SystemStatus(
                status=status,
                created_at=now
            )
            session.add(new_status)
            await session.commit()
            self.logger.log_white_multiple(
                "[system status dao] recorded status change: ", status)

    async def read_latest_status(self):
        """
        Reads the most recent system status entry from the database.

        Returns:
            The most recent SystemStatus object or None if no entries exist
        """

        # Find the maximum ID which will be the most recently inserted record
        max_id_subquery = select(func.max(SystemStatus.id)).scalar_subquery()
        query = select(SystemStatus).where(SystemStatus.id == max_id_subquery)

        async with self.session_maker() as session:
            result = await session.execute(query)
            latest_status = result.scalar_one_or_none()

            if latest_status:
                return latest_status.status
            else:
                self.logger.log_purple("[dao] None status")
                return None
