# daily_summary_dao.py
import traceback
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker
from datetime import datetime, timedelta
from typing import List

from ...util.errors import SuspiciousDurationError

from ...config.definitions import power_on_off_debug_file

from ..models import DailyDomainSummary
from ...util.console_logger import ConsoleLogger
from ...object.classes import ChromeSessionData

# @@@@ @@@@ @@@@ @@@@ @@@@
# NOTE: Does not use BaseQueueDao - Because ... <insert reason here when recalled>
# @@@@ @@@@ @@@@ @@@@ @@@@


class ChromeSummaryDao:  # NOTE: Does not use BaseQueueDao
    def __init__(self,  chrome_logging_dao, session_maker: async_sessionmaker, batch_size=100, flush_interval=5):
        self.chrome_logging_dao = chrome_logging_dao
        self.session_maker = session_maker  # Store the session maker instead of db
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.logger = ConsoleLogger()

    async def create_if_new_else_update(self, chrome_session: ChromeSessionData, right_now: datetime, is_shutdown=False):
        """This method doesn't use queuing since it needs to check the DB state"""
        target_domain_name = chrome_session.domain

        # ### Calculate time difference
        if chrome_session.start_time is None or chrome_session.end_time is None:
            raise ValueError("Start or end time was None")
        if chrome_session.duration is None:
            raise ValueError("Session duration was None")
        usage_duration_in_hours = chrome_session.duration.total_seconds() / 3600

        # ### Check if entry exists for today
        today = right_now.replace(hour=0, minute=0, second=0,
                                  microsecond=0)  # Still has tz attached
        query = select(DailyDomainSummary).where(
            DailyDomainSummary.domain_name == target_domain_name,
            DailyDomainSummary.gathering_date >= today,
            DailyDomainSummary.gathering_date < today + timedelta(days=1)
        )

        self.chrome_logging_dao.create_log(chrome_session, right_now)

        async with self.session_maker() as session:
            result = await session.execute(query)
            # existing_entry = await result.scalar_one_or_none()  # Adding await here makes the program fail
            # This is how it is properly done, this unawaited version works
            existing_entry = result.scalar_one_or_none()
            # self.logger.log_yellow_multiple(
            #     "[debug]", str(chrome_session.duration))
            if existing_entry:

                if chrome_session.duration and chrome_session.duration > timedelta(hours=1):
                    self.logger.log_red(
                        "[critical - duration] " + str(chrome_session.duration) + " for " + existing_entry.domain_name)
                    raise SuspiciousDurationError("duration")

                impossibly_long_day = existing_entry.hours_spent > 16
                if impossibly_long_day:
                    self.logger.log_red(
                        "[critical - long day] " + str(existing_entry.hours_spent) + " for " + existing_entry.domain_name)
                    raise SuspiciousDurationError("long day")

                # TODO: If duration > some_sus_threshold, throw err
                self.logger.log_white_multiple("[chrome summary dao] adding time ",
                                               chrome_session.duration, " to ", existing_entry.domain_name)
                existing_entry.hours_spent += usage_duration_in_hours
                await session.commit()
            else:
                print("[debug] NEW session: ",
                      chrome_session.domain, usage_duration_in_hours, chrome_session.start_time.day)
                await self.create(target_domain_name, usage_duration_in_hours, today)
        if is_shutdown:
            with open(power_on_off_debug_file, "a") as f:
                f.write("shutting down Chrome summary dao")
                f.write("\n")

    async def create(self, target_domain_name, duration_in_hours, when_it_was_gathered):
        async with self.session_maker() as session:
            new_entry = DailyDomainSummary(
                domain_name=target_domain_name,
                hours_spent=duration_in_hours,
                gathering_date=when_it_was_gathered
            )
            session.add(new_entry)
            await session.commit()

    async def read_past_week(self, right_now: datetime):
        # today = self.system_clock.now()

        # +1 because weekday() counts from Monday=0
        days_since_sunday = right_now.weekday() + 1
        last_sunday = right_now - timedelta(days=days_since_sunday)
        query = select(DailyDomainSummary).where(
            func.date(DailyDomainSummary.gathering_date) >= last_sunday.date()
        )

        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()

    async def read_past_month(self, right_now: datetime):
        """Read all entries from the 1st of the current month through today."""
        # today = self.system_clock.now()
        start_of_month = right_now.replace(day=1)  # First day of current month

        query = select(DailyDomainSummary).where(
            func.date(DailyDomainSummary.gathering_date) >= start_of_month.date()
        )

        async with self.session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()

    async def read_day(self, day: datetime) -> List[DailyDomainSummary]:
        """Read all entries for the given day."""
        today_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)

        query = select(DailyDomainSummary).where(
            DailyDomainSummary.gathering_date >= today_start,
            DailyDomainSummary.gathering_date < tomorrow_start
        )
        async with self.session_maker() as session:

            result = await session.execute(query)
            return result.scalars().all()

    async def read_all(self):
        """Read all entries."""
        async with self.session_maker() as session:
            result = await session.execute(select(DailyDomainSummary))
            return result.scalars().all()

    async def read_row_for_domain(self, target_domain: str, right_now: datetime):
        """Reads the row for the target program for today."""
        today_start = right_now.replace(
            hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)

        query = select(DailyDomainSummary).where(
            DailyDomainSummary.program_name == target_domain,
            DailyDomainSummary.gathering_date >= today_start,
            DailyDomainSummary.gathering_date < tomorrow_start
        )
        async with self.session_maker() as session:
            result = await session.execute(query)
            return await result.scalar_one_or_none()

    async def shutdown(self):
        """Closes the open session without opening a new one"""

        pass

    async def delete(self, id: int):
        """Delete an entry by ID"""
        async with self.session_maker() as session:
            entry = await session.get(DailyDomainSummary, id)
            if entry:
                await session.delete(entry)
                await session.commit()
            return entry
