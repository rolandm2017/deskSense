from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, desc, func
from datetime import datetime
import asyncpg

from ...db.database import SQLALCHEMY_DATABASE_URL, SYNCHRONOUS_DB_URL

from ...object.enums import SystemStatusType
from ...util.console_logger import ConsoleLogger
from ..models import SystemStatus


class SystemStatusDao:
    """
    Does NOT use the queue because read/write here
    should always always get priority, i.e. no queue!
    """

    def __init__(self, async_session_maker: async_sessionmaker, sync_session_maker: sessionmaker, batch_size=100, flush_interval=5):
        """ Exists mostly for debugging. """
        self.async_session_maker = async_session_maker
        self.shutdown_session_maker = sync_session_maker
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.logger = ConsoleLogger()
        self.power_tracker_loop = None
        self.emerg_connection_string = SYNCHRONOUS_DB_URL

    def accept_power_tracker_loop(self, loop):
        """Set the event loop to use for power tracker operations. Means it's shared with whatever did the insert"""
        print(f"DAO accepting new event loop for power tracking")
        self.power_tracker_loop = loop

    async def create_status(self, status: SystemStatusType, now: datetime):
        """Create a status entry with awareness of which event loop to use"""
        # Select the appropriate session maker based on status type
        status_to_write = status
        try:
            if status == SystemStatusType.STARTUP:
                latest_status = await self.read_latest_status()
                print("[info] Found status: ", latest_status)
                if latest_status == SystemStatusType.HOT_RELOAD_STARTED:
                    status_to_write = SystemStatusType.HOT_RELOAD_CONCLUDED
                    # TODO: If status is a hot reload, make the concluding entry delete both, for cleanliness
                    # return self.clean_hot_reload_entry(latest_status_id)

            critical_statuses = [
                SystemStatusType.HOT_RELOAD_STARTED,
                SystemStatusType.CTRL_C_SIGNAL,
                SystemStatusType.SHUTDOWN,
                SystemStatusType.SLEEP
            ]

            if status in critical_statuses:
                print(
                    f"Using synchronous SQLAlchemy for critical status: {status}")
                # Use synchronous session in the current thread
                return self.write_sync(status_to_write, now)

            else:
                return await self.async_write(status_to_write, now)

        except Exception as e:
            print(f"Error in create_status: {e}")
            import traceback
            traceback.print_exc()
            # Don't re-raise - this is critical shutdown code

    def write_sync(self, status: SystemStatusType, now: datetime):
        with self.shutdown_session_maker() as session:
            new_status = SystemStatus(
                status=status,
                created_at=now
            )
            session.add(new_status)
            session.commit()
            print("Synchronous database commit successful")
            self.logger.log_white_multiple(
                "[system status dao] recorded status change: ", status)
            return True

    async def async_write(self, status: SystemStatusType, now: datetime):
        async with self.async_session_maker() as session:
            new_status = SystemStatus(
                status=status,
                created_at=now
            )
            session.add(new_status)
            await session.commit()
            print("Database commit successful")
            self.logger.log_white_multiple(
                "[system status dao] recorded status change: ", status)
            return True

    async def emergency_write(self, status: SystemStatusType, now: datetime):
        """
        Emergency write method that creates its own connection for shutdown scenarios.
        Uses raw asyncpg to avoid event loop issues.

        🙌
        """

        # NOTE: This IS NOT a method you "just use". Am trying to move away from using it. Use write_sync and async_write.

        print(f"[EMERGENCY] Writing {status} to database")

        try:
            # Create a fresh connection
            conn = await asyncpg.connect(self.emerg_connection_string)

            # Map Python enum value to database enum value (convert to uppercase)
            # Use the enum name which is uppercase (e.g., CTRL_C_SIGNAL)
            db_status = status.name

            print("writing " + db_status + " :: ")

            # Direct SQL insert without SQLAlchemy
            await conn.execute(
                "INSERT INTO system_change_log (status, created_at) VALUES ($1, $2)",
                db_status, now
            )

            # Close connection
            await conn.close()

            print(f"[EMERGENCY] Successfully wrote {status} to database")
            self.logger.log_white_multiple(
                "[system status dao] recorded status change (emergency): ", status)

            return True
        except Exception as e:
            print(f"[EMERGENCY] Failed to write {status}: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def read_latest_status(self):
        """Reads the most recent system status entry from the database."""
        try:
            max_id_subquery = select(
                func.max(SystemStatus.id)).scalar_subquery()
            query = select(SystemStatus).where(
                SystemStatus.id == max_id_subquery)

            async with self.async_session_maker() as session:  # Use regular session maker
                result = await session.execute(query)
                latest_status = result.scalar_one_or_none()

                if latest_status:
                    return latest_status.status
                else:
                    self.logger.log_purple("[dao] None status")
                    return None
        except Exception as e:
            print(f"Error reading latest status: {e}")
            return None

    async def read_latest_shutdown(self) -> SystemStatus | None:
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

            async with self.async_session_maker() as session:
                result = await session.execute(query)
                latest_status = result.scalar_one_or_none()

                if latest_status:
                    self.logger.log_white_multiple(
                        "[dao] Found latest shutdown status: ", latest_status.status)
                    return latest_status
                else:
                    self.logger.log_purple("[dao] No shutdown status found")
                    return None
        except Exception as e:
            print(f"Error reading latest shutdown status: {e}")
            import traceback
            traceback.print_exc()
            return None
