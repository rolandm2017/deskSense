# daily_summary_dao.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker

import traceback
from datetime import datetime, timedelta, time
from typing import List

from surveillance.src.config.definitions import power_on_off_debug_file

from surveillance.src.db.models import DailyDomainSummary
from surveillance.src.object.classes import ChromeSession

from surveillance.src.util.console_logger import ConsoleLogger
from surveillance.src.util.dao_wrapper import validate_start_end_and_duration, validate_start_and_end_times
from surveillance.src.util.errors import NegativeTimeError, ImpossibleToGetHereError
from surveillance.src.util.debug_util import notice_suspicious_durations, log_if_needed
from surveillance.src.util.const import SECONDS_PER_HOUR
from surveillance.src.util.time_formatting import get_start_of_day
from surveillance.src.util.time_wrappers import UserLocalTime


# @@@@ @@@@ @@@@ @@@@ @@@@
# NOTE: Does not use BaseQueueDao - Because ... <insert reason here when recalled>
# @@@@ @@@@ @@@@ @@@@ @@@@


class ChromeSummaryDao:  # NOTE: Does not use BaseQueueDao
    def __init__(self,  chrome_logging_dao, regular_session: sessionmaker, async_session_maker: async_sessionmaker):
        self.chrome_logging_dao = chrome_logging_dao
        self.debug = False
        self.regular_session = regular_session
        self.async_session_maker = async_session_maker
        self.logger = ConsoleLogger()

    def start_session(self, chrome_session: ChromeSession, right_now):
        target_domain_name = chrome_session.domain

        starting_window_amt = 10  # sec
        usage_duration_in_hours = starting_window_amt / SECONDS_PER_HOUR

        today = right_now.replace(hour=0, minute=0, second=0,
                                  microsecond=0)  # Still has tz attached
        self._create(target_domain_name, usage_duration_in_hours, today)

    def _create(self, target_domain_name, duration_in_hours, when_it_was_gathered):
        print(
            f"creating for {target_domain_name} with duration {duration_in_hours * SECONDS_PER_HOUR}")
        self.throw_if_negative(target_domain_name, duration_in_hours)
        with self.regular_session() as session:
            new_entry = DailyDomainSummary(
                domain_name=target_domain_name,
                hours_spent=duration_in_hours,
                gathering_date=when_it_was_gathered
            )
            session.add(new_entry)
            session.commit()

    def find_todays_entry_for_domain(self, chrome_session: ChromeSession):
        if chrome_session.start_time is None:
            raise ValueError("start_time was not set")

        start_time = chrome_session.start_time.dt
        start_of_day = datetime.combine(
            start_time.date(), time.min, tzinfo=start_time.tzinfo)
        end_of_day = datetime.combine(
            start_time.date(), time.max, tzinfo=start_time.tzinfo)

        query = select(DailyDomainSummary).where(
            DailyDomainSummary.domain_name == chrome_session.domain,
            DailyDomainSummary.gathering_date >= start_of_day,
            DailyDomainSummary.gathering_date < end_of_day
        )

        return self.exec_and_read_one_or_none(query)

    def read_row_for_domain(self, target_domain_name, right_now):
        today = right_now.replace(hour=0, minute=0, second=0,
                                  microsecond=0)  # Still has tz attached
        query = select(DailyDomainSummary).where(
            DailyDomainSummary.domain_name == target_domain_name,
            DailyDomainSummary.gathering_date >= today,
            DailyDomainSummary.gathering_date < today + timedelta(days=1)
        )
        with self.regular_session() as session:
            result = session.execute(query)
            return result.scalar_one_or_none()

    def read_past_week(self, right_now: UserLocalTime):

        # +1 because weekday() counts from Monday=0
        days_since_sunday = right_now.dt.weekday() + 1
        last_sunday = right_now.dt - timedelta(days=days_since_sunday)
        query = select(DailyDomainSummary).where(
            func.date(DailyDomainSummary.gathering_date) >= last_sunday.date()
        )

        with self.regular_session() as session:
            result = session.execute(query)
            return result.scalars().all()

    def read_past_month(self, right_now: UserLocalTime):
        """Read all entries from the 1st of the current month through today."""
        start_of_month = right_now.dt.replace(
            day=1)  # First day of current month

        query = select(DailyDomainSummary).where(
            func.date(DailyDomainSummary.gathering_date) >= start_of_month.date()
        )

        with self.regular_session() as session:
            result = session.execute(query)
            return result.scalars().all()

    def read_day(self, day: UserLocalTime) -> List[DailyDomainSummary]:
        """Read all entries for the given day."""
        today_start = get_start_of_day(day.dt)
        tomorrow_start = today_start + timedelta(days=1)

        query = select(DailyDomainSummary).where(
            DailyDomainSummary.gathering_date >= today_start,
            DailyDomainSummary.gathering_date < tomorrow_start
        )
        with self.regular_session() as session:
            result = session.execute(query)
            result = result.scalars().all()
            return list(result)

    def read_all(self):
        """Read all entries."""
        with self.regular_session() as session:
            result = session.execute(select(DailyDomainSummary))
            return result.scalars().all()

    def update_hours(self, existing_entry, usage_duration_in_hours):
        with self.regular_session() as session:
            # Reattach the entity to the current session if it's detached
            if existing_entry not in session:
                existing_entry = session.merge(existing_entry)

            # Update the hours
            new_duration = existing_entry.hours_spent + usage_duration_in_hours
            self.throw_if_negative(existing_entry.domain_name, new_duration)
            existing_entry.hours_spent = new_duration

            # Commit the changes
            session.commit()

    def push_window_ahead_ten_sec(self, chrome_session: ChromeSession, right_now):
        """Finds the given session and adds ten sec to its end_time

        NOTE: This only ever happens after start_session
        """
        target_domain = chrome_session.domain
        today_start = get_start_of_day(right_now)
        tomorrow_start = today_start + timedelta(days=1)

        query = select(DailyDomainSummary).where(
            DailyDomainSummary.domain_name == target_domain,
            DailyDomainSummary.gathering_date >= today_start,
            DailyDomainSummary.gathering_date < tomorrow_start
        )
        with self.regular_session() as db_session:
            domain: DailyDomainSummary = db_session.scalars(query).first()
            # FIXME: Sometimes domain is none
            if domain:
                domain.hours_spent = domain.hours_spent + 10 / SECONDS_PER_HOUR
                db_session.commit()
            else:
                raise ImpossibleToGetHereError(
                    "A domain should already exist here, but was not found")

    def deduct_remaining_duration(self, session: ChromeSession, duration_in_sec: int, today_start):
        """
        When a session is concluded, it was concluded partway thru the 10 sec window

        9 times out of 10. So we deduct the unfinished duration from its hours_spent.
        """
        print(session, "160ru")
        print(duration_in_sec, "161ru")
        target_domain = session.domain

        tomorrow_start = today_start + timedelta(days=1)

        query = select(DailyDomainSummary).where(
            DailyDomainSummary.domain_name == target_domain,
            DailyDomainSummary.gathering_date >= today_start,
            DailyDomainSummary.gathering_date < tomorrow_start
        )
        # Update it if found
        with self.regular_session() as db_session:
            domain: DailyDomainSummary = db_session.scalars(query).first()
            new_duration = domain.hours_spent - duration_in_sec / SECONDS_PER_HOUR
            self.throw_if_negative(domain.domain_name, new_duration)
            domain.hours_spent = new_duration
            db_session.commit()

    def exec_and_read_one_or_none(self, query):
        """Helper method to make code more testable and pleasant to read"""
        with self.regular_session() as session:
            result = session.execute(query)
            return result.scalar_one_or_none()

    def throw_if_negative(self, activity, value):
        if value < 0:
            raise NegativeTimeError(activity, value)

    async def shutdown(self):
        """Closes the open session without opening a new one"""

        pass

    async def delete(self, id: int):
        """Delete an entry by ID"""
        async with self.regular_session() as session:
            entry = await session.get(DailyDomainSummary, id)
            if entry:
                await session.delete(entry)
                await session.commit()
            return entry
