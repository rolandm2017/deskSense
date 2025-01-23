from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from datetime import datetime, timedelta

from .base_dao import BaseQueueingDao
from ..models import Program
from ...object.classes import ProgramSessionData
from ...console_logger import ConsoleLogger


class ChromeDao(BaseQueueingDao):
    # TODO
    def __init__(self, session_maker: async_sessionmaker, batch_size=100, flush_interval=5):
        super().__init__(session_maker, batch_size, flush_interval)
        self.logger = ConsoleLogger()

    def create(self, url_delivery):
        pass

    def read(self):
        pass

    def delete(self):
        pass
