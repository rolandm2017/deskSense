# session_integrity_dao.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker
from datetime import datetime, timedelta
from typing import List

from activitytracker.db.models import DomainSummaryLog, ProgramSummaryLog
from activitytracker.util.console_logger import ConsoleLogger
from activitytracker.util.debug_logger import print_and_log


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

    def audit_sessions(self, latest_shutdown_time: datetime, startup_time: datetime):
        """
        Perform integrity checks on session data against system power states.

        Runs every time the program starts, unless it's a hot reload I guess.
        """
        program_orphans, domain_orphans = self.find_orphans(
            latest_shutdown_time, startup_time)
        program_phantoms, domain_phantoms = self.find_phantoms(
            latest_shutdown_time, startup_time)
        a = len(program_orphans)
        b = len(domain_orphans)
        c = len(program_phantoms)
        d = len(domain_phantoms)
        if a == 0 and b == 0 and c == 0 and d == 0:
            self.logger.log_white_multiple(
                "[info] Orphans and phantoms: 0, 0, 0, 0")
        else:
            self.logger.log_red_multiple(
                "[debug] Orphans and phantoms found:", a, b, c, d)
            self.logger.log_red("[debug] Program was offline between " +
                                str(latest_shutdown_time) + " and " + str(startup_time))
            print_and_log(program_orphans, latest_shutdown_time, startup_time)
            print_and_log(domain_orphans, latest_shutdown_time, startup_time)
            print_and_log(program_phantoms, latest_shutdown_time, startup_time)
            print_and_log(domain_phantoms, latest_shutdown_time, startup_time)

    def find_orphans(self, latest_shutdown: datetime, startup_time: datetime):
        """Find sessions that were never properly closed -- still open after shutdown."""
        # Implementation that uses system_status_dao to get power events
        # and checks against program/chrome logs
        programs: List[ProgramSummaryLog] = self.program_logging_dao.find_orphans(
            latest_shutdown, startup_time)
        domains: List[DomainSummaryLog] = self.chrome_logging_dao.find_orphans(
            latest_shutdown, startup_time)
        return programs, domains

    def find_phantoms(self, latest_shutdown: datetime, startup_time: datetime):
        """
        Find sessions that started during system power-off periods
        A phantom is a session that has its start time as "when the computer was surely off."
        """
        # Implementation that checks for session start times during power-off periods
        programs: List[ProgramSummaryLog] = self.program_logging_dao.find_phantoms(
            latest_shutdown, startup_time)
        domains: List[DomainSummaryLog] = self.chrome_logging_dao.find_phantoms(
            latest_shutdown, startup_time)
        return programs, domains

    def audit_first_startup(self, startup_time: datetime):
        the_beginning_of_time = datetime.min
        program_orphans, domain_orphans = self.find_orphans(
            the_beginning_of_time, startup_time)
        program_phantoms, domain_phantoms = self.find_phantoms(
            the_beginning_of_time, startup_time)
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
            print_and_log(program_orphans, the_beginning_of_time, startup_time)
            print_and_log(domain_orphans, the_beginning_of_time, startup_time)
            print_and_log(program_phantoms,
                          the_beginning_of_time, startup_time)
            print_and_log(domain_phantoms, the_beginning_of_time, startup_time)
