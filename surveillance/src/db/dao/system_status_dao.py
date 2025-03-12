from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import select, desc, func
import asyncio
from datetime import datetime
import asyncpg

from ...db.database import SQLALCHEMY_DATABASE_URL

from ...object.enums import SystemStatusType
from ...util.console_logger import ConsoleLogger
from ..models import SystemStatus


class SystemStatusDao:
    """
    Does NOT use the queue because read/write here
    should always always get priority, i.e. no queue!
    """

    def __init__(self, session_maker: async_sessionmaker, shutdown_session_maker, batch_size=100, flush_interval=5):
        """ Exists mostly for debugging. """
        self.session_maker = session_maker
        self.shutdown_session_maker = shutdown_session_maker
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.logger = ConsoleLogger()
        self.power_tracker_loop = None
        self.connection_string = None

        if SQLALCHEMY_DATABASE_URL and '+asyncpg' in SQLALCHEMY_DATABASE_URL:
            self.connection_string = SQLALCHEMY_DATABASE_URL.replace(
                '+asyncpg', '')
        else:
            self.connection_string = SQLALCHEMY_DATABASE_URL

    def accept_power_tracker_loop(self, loop):
        """Set the event loop to use for power tracker operations"""
        print(f"DAO accepting new event loop for power tracking")
        self.power_tracker_loop = loop

    async def create_status(self, status: SystemStatusType, now: datetime):
        """Create a status entry with awareness of which event loop to use"""
        print(f"[debug - create_status] {status}, type: {type(status)}")

        # Select the appropriate session maker based on status type
        if status in [SystemStatusType.SHUTDOWN, SystemStatusType.CTRL_C_SIGNAL,
                      SystemStatusType.HOT_RELOAD_STARTED, SystemStatusType.SLEEP]:
            session_maker = self.shutdown_session_maker
            print(f"Using shutdown session maker for {status}")
        else:
            session_maker = self.session_maker
            print(f"Using regular session maker for {status}")

        try:
            # Process STARTUP/HOT_RELOAD logic
            if status == SystemStatusType.STARTUP:
                latest_status = await self.read_latest_status()
                print("[info] Found status: ", latest_status)
                if latest_status == SystemStatusType.HOT_RELOAD_STARTED:
                    # It's not only a STARTUP, it's recovering from a hot reload.
                    status = SystemStatusType.HOT_RELOAD_RECOVERY

            print(f"Writing status to database: {status}")

            # Create and use a session bound to the appropriate session maker
            async with session_maker() as session:
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

    async def emergency_write(self, status: SystemStatusType, now: datetime):
        """
        Emergency write method that creates its own connection for shutdown scenarios.
        Uses raw asyncpg to avoid event loop issues.

        🙌
        """
        print(f"[EMERGENCY] Writing {status} to database")

        try:
            # Create a fresh connection
            conn = await asyncpg.connect(self.connection_string)

            # Map Python enum value to database enum value (convert to uppercase)
            # Use the enum name which is uppercase (e.g., CTRL_C_SIGNAL)
            db_status = status.name

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

            async with self.session_maker() as session:  # Use regular session maker
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
