from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, desc, func
from datetime import datetime
import asyncpg

from activitytracker.db.database import SQLALCHEMY_DATABASE_URL, SYNCHRONOUS_DB_URL
from activitytracker.db.dao.utility_dao_mixin import UtilityDaoMixin


# from activitytracker.object.enums import SystemStatusType
from activitytracker.object.enums import SystemStatusType
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.db.models import SystemStatus
from activitytracker.util.time_wrappers import UserLocalTime


class SystemStatusDao(UtilityDaoMixin):
    """
    Exists to use polling to tell when the program is up and running.

    Intent is to create an auditable time to check summaries against.
    """

    def __init__(self, sync_session_maker: sessionmaker):
        """ Exists mostly for debugging. """
        self.shutdown_session_maker = sync_session_maker
        self.logger = ConsoleLogger()

    def add_new(self):
        """
        Writes the current timestamp to the table.
        """
        pass
