# session_integrity_dao.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker
from datetime import datetime, timedelta
from typing import List

from ..models import DailyDomainSummary, DailyProgramSummary
from ...object.classes import ChromeSessionData
from ...util.console_logger import ConsoleLogger
from ...util.debug_logger import print_and_log


class SessionIntegrityDao:
    def __init__(self,
                 #  system_status_dao,
                 program_logging_dao,
                 chrome_logging_dao,
                 session_maker: async_sessionmaker):
        # self.system_status_dao = system_status_dao
        self.program_logging_dao = program_logging_dao
        self.chrome_logging_dao = chrome_logging_dao
        self.session_maker = session_maker
        self.logger = ConsoleLogger()

    async def audit_sessions(self, latest_shutdown: datetime, startup_time: datetime):
        """
        Perform integrity checks on session data against system power states.

        Runs every time the program starts, unless it's a hot reload I guess.
        """
        program_orphans, domain_orphans = await self.find_orphans(latest_shutdown, startup_time)
        program_phantoms, domain_phantoms = await self.find_phantoms(latest_shutdown, startup_time)
        a = len(program_orphans)
        b = len(domain_orphans)
        c = len(program_phantoms)
        d = len(domain_phantoms)
        if a == 0 and b == 0 and c == 0 and d == 0:
            self.logger.log_white_multiple(
                "[info] Orphans and phantoms: 0, 0, 0, 0")
        else:
            self.logger.log_red_multiple(
                "Orphans and phantoms found:", a, b, c, d)
        print_and_log(program_orphans, startup_time)
        print_and_log(domain_orphans, startup_time)
        print_and_log(program_phantoms, startup_time)
        print_and_log(domain_phantoms, startup_time)

    async def find_orphans(self, latest_shutdown: datetime, startup_time: datetime):
        """Find sessions that were never properly closed -- still open after shutdown."""
        # Implementation that uses system_status_dao to get power events
        # and checks against program/chrome logs
        programs: List[DailyProgramSummary] = await self.program_logging_dao.find_orphans(
            latest_shutdown, startup_time)
        domains: List[DailyDomainSummary] = await self.chrome_logging_dao.find_orphans(latest_shutdown, startup_time)
        return programs, domains

    async def find_phantoms(self, latest_shutdown: datetime, startup_time: datetime):
        """
        Find sessions that started during system power-off periods
        A phantom is a session that has its start time as "when the computer was surely off."
        """
        # Implementation that checks for session start times during power-off periods
        programs: List[DailyProgramSummary] = await self.program_logging_dao.find_phantoms(
            latest_shutdown, startup_time)
        domains: List[DailyDomainSummary] = await self.chrome_logging_dao.find_phantoms(latest_shutdown, startup_time)
        return programs, domains
