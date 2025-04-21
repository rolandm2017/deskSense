from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, desc, func
from datetime import datetime
import asyncpg

from surveillance.src.db.database import SQLALCHEMY_DATABASE_URL, SYNCHRONOUS_DB_URL

# from surveillance.src.object.enums import SystemStatusType
from surveillance.src.object.enums import SystemStatusType
from surveillance.src.util.console_logger import ConsoleLogger
from surveillance.src.db.models import SystemStatus
from surveillance.src.util.time_wrappers import UserLocalTime


class SystemStatusDao:
    """
    Does NOT use the queue because read/write here
    should always always get priority, i.e. no queue!
    """

    def __init__(self, sync_session_maker: sessionmaker, async_session_maker: async_sessionmaker, batch_size=100, flush_interval=1):
        """ Exists mostly for debugging. """
        self.shutdown_session_maker = sync_session_maker
        self.async_session_maker = async_session_maker
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.logger = ConsoleLogger()
        self.power_tracker_loop = None
        self.emerg_connection_string = SYNCHRONOUS_DB_URL

    def accept_power_tracker_loop(self, loop):
        """Set the event loop to use for power tracker operations. Means it's shared with whatever did the insert"""
        print(f"DAO accepting new event loop for power tracking")
        self.power_tracker_loop = loop

    async def create_status(self, status: SystemStatusType, now: UserLocalTime):
        """Create a status entry with awareness of which event loop to use"""
        # TODO: The critical status -> write_sync path never overlaps with the noncritical -> async_write
        # TODO: So you can branch before this method into create_status_sync and create_status_async
        # Select the appropriate session maker based on status type
        status_to_write = status
        try:
            if status == SystemStatusType.STARTUP:
                latest_status = self.read_latest_status()
                print("[info] Found status: ", latest_status)
                if latest_status == SystemStatusType.HOT_RELOAD_STARTED:
                    status_to_write = SystemStatusType.HOT_RELOAD_CONCLUDED
                    # TODO: If status is a hot reload, make the concluding entry delete both, for cleanliness
                    # TODO: ...because I don't need to see a long chain of offline->online 4 seconds apart
                    # return self.clean_hot_reload_entry(latest_status_id)

            critical_statuses = [
                SystemStatusType.HOT_RELOAD_STARTED,
                SystemStatusType.CTRL_C_SIGNAL,
                SystemStatusType.SHUTDOWN,
                SystemStatusType.SLEEP
            ]

            if status_to_write in critical_statuses:
                print(
                    f"Using synchronous SQLAlchemy for critical status: {status}")
                # Use synchronous session in the current thread
                new_status_obj_to_write = SystemStatus(
                    status=status_to_write,
                    created_at=now.dt
                )
                return self.write_sync(new_status_obj_to_write, now)

            else:
                new_status_obj = SystemStatus(
                    status=status_to_write,
                    created_at=now.dt
                )
                return await self.async_write(new_status_obj, now)

        except Exception as e:
            print(f"Error in create_status: {e}")
            import traceback
            traceback.print_exc()
            # Don't re-raise - this is critical shutdown code

    def write_sync(self, status: SystemStatus, now: UserLocalTime):
        with self.shutdown_session_maker() as session:
            session.add(status)
            session.commit()
            print("Synchronous database commit successful")
            self.logger.log_white_multiple(
                "[system status dao] recorded status change: ", status)
            return True

    async def async_write(self, status: SystemStatus, now: UserLocalTime):
        async with self.async_session_maker() as session:
            session.add(status)
            await session.commit()
            print("Database commit successful")
            self.logger.log_white_multiple(
                "[system status dao] recorded status change: ", status)
            return True

    def read_latest_status(self):
        """Reads the most recent system status entry from the database."""
        try:
            max_id_subquery = select(
                func.max(SystemStatus.id)).scalar_subquery()
            query = select(SystemStatus).where(
                SystemStatus.id == max_id_subquery)

            some_status: SystemStatus | None = self.read_latest_status_from_db(
                query)
            if some_status:
                return some_status.status
            else:
                self.logger.log_purple("[dao] None status")
                return None
        except Exception as e:
            print(f"Error reading latest status: {e}")
            return None

    def read_latest_shutdown(self) -> SystemStatus | None:
        try:
            # Query the latest status entry where status is one of the shutdown types
            query = select(SystemStatus).where(
                SystemStatus.status.in_([
                    SystemStatusType.SHUTDOWN,
                    SystemStatusType.CTRL_C_SIGNAL,
                    SystemStatusType.HOT_RELOAD_STARTED,
                    SystemStatusType.SLEEP
                ])
            ).order_by(desc(SystemStatus.created_at)).limit(1)

            some_status = self.read_latest_status_from_db(query)
            if some_status:
                self.logger.log_white_multiple(
                    "[dao] Found latest shutdown status: ", some_status.status)
                return some_status
            else:
                self.logger.log_purple("[dao] No status found")
                return None
        except Exception as e:
            print(f"Error reading latest shutdown status: {e}")
            import traceback
            traceback.print_exc()
            return None

    def read_latest_status_from_db(self, query) -> SystemStatus | None:
        with self.shutdown_session_maker() as session:
            result = session.execute(query)
            latest_status = result.scalar_one_or_none()

            if latest_status:
                self.logger.log_white_multiple(
                    "[dao] Found latest status: ", latest_status.status)
                return latest_status
            else:
                self.logger.log_purple("[dao] No status found")
                return None
