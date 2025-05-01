# daily_summary_dao.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker

import traceback
from datetime import datetime, timedelta, time
from typing import List

from surveillance.src.config.definitions import keep_alive_cycle_length, window_push_length 
from surveillance.src.db.dao.utility_dao_mixin import UtilityDaoMixin
from surveillance.src.db.models import DailyDomainSummary
from surveillance.src.object.classes import ChromeSession

from surveillance.src.util.console_logger import ConsoleLogger
from surveillance.src.util.errors import NegativeTimeError, ImpossibleToGetHereError
from surveillance.src.util.const import SECONDS_PER_HOUR
from surveillance.src.util.time_formatting import get_start_of_day_from_datetime, attach_tz_to_all, attach_tz_to_obj
from surveillance.src.util.time_wrappers import UserLocalTime


# @@@@ @@@@ @@@@ @@@@ @@@@
# NOTE: Does not use BaseQueueDao - Because ... <insert reason here when recalled>
# @@@@ @@@@ @@@@ @@@@ @@@@


class ChromeSummaryDao(UtilityDaoMixin):  # NOTE: Does not use BaseQueueDao
    def __init__(self,  chrome_logging_dao, regular_session: sessionmaker):
        self.chrome_logging_dao = chrome_logging_dao
        self.debug = False
        self.regular_session = regular_session
        self.logger = ConsoleLogger()

    def start_session(self, chrome_session: ChromeSession):
        target_domain_name = chrome_session.domain

        usage_duration_in_hours = 0  # start_session no longer adds time. It's all add_ten_sec

        self._create(target_domain_name, chrome_session.start_time.dt)

    def _create(self, target_domain_name, start_time_dt: datetime):
        # self.logger.log_white(
        #     f"[info] creating for {target_domain_name} with duration {duration_in_hours * SECONDS_PER_HOUR}")
        today = get_start_of_day_from_datetime(start_time_dt)  # Still has tz attached
        
        new_entry = DailyDomainSummary(
            domain_name=target_domain_name,
            hours_spent=0,
            gathering_date=today,
            gathering_date_local = start_time_dt.replace(tzinfo=None)
        )
        self.add_new_item(new_entry)

    def find_todays_entry_for_domain(self, chrome_session: ChromeSession) -> DailyDomainSummary | None:
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

        result = self.execute_and_read_one_or_none(query)

        if result is None:
            return None  # Or create a default
            
        return attach_tz_to_obj(result, chrome_session.start_time.dt.tzinfo)

    def read_past_week(self, right_now: UserLocalTime):

        # +1 because weekday() counts from Monday=0
        days_since_sunday = right_now.dt.weekday() + 1
        last_sunday = right_now.dt - timedelta(days=days_since_sunday)
        query = select(DailyDomainSummary).where(
            func.date(DailyDomainSummary.gathering_date) >= last_sunday.date()
        )
        result = self.execute_and_return_all(query)
        return attach_tz_to_all(result, right_now.dt.tzinfo)


    def read_day(self, day: UserLocalTime) -> List[DailyDomainSummary]:
        """Read all entries for the given day."""
        today_start = get_start_of_day_from_datetime(day.dt)
        tomorrow_start = today_start + timedelta(days=1)

        query = select(DailyDomainSummary).where(
            DailyDomainSummary.gathering_date >= today_start,
            DailyDomainSummary.gathering_date < tomorrow_start
        )
        result = self.execute_and_return_all(query)
        return attach_tz_to_all(result, day.dt.tzinfo)

    def read_all(self):
        """Read all entries."""
        query = select(DailyDomainSummary)
        # Developer handles it manually
        return self.execute_and_return_all(query)
    
    def select_where_time_equals(self, some_time):
        return select(DailyDomainSummary).where(
            DailyDomainSummary.gathering_date.op('=')(some_time)
        )


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


    def push_window_ahead_ten_sec(self, chrome_session: ChromeSession):
        """Finds the given session and adds ten sec to its end_time

        NOTE: This only ever happens after start_session
        """
        target_domain = chrome_session.domain
        today_start = get_start_of_day_from_datetime(chrome_session.start_time.dt)

        query = self.select_where_time_equals(today_start)
        self.execute_window_push(query)

    def execute_window_push(self, query):
        with self.regular_session() as db_session:
            # TODO: change to "Update hours"
            domain: DailyDomainSummary = db_session.scalars(query).first()
            # FIXME: Sometimes domain is none
            if domain:
                domain.hours_spent = domain.hours_spent + window_push_length / SECONDS_PER_HOUR
                db_session.commit()
            else:
                raise ImpossibleToGetHereError(
                    "A domain should already exist here, but was not found")

    def add_used_time(self, session: ChromeSession, duration_in_sec: int, today_start: UserLocalTime):
        """
        When a session is concluded, it was concluded partway thru the 10 sec window

        9 times out of 10. So we deduct the unfinished duration from its hours_spent.
        """
        if duration_in_sec == 0:
            return  # No work to do here
        tomorrow_start = today_start.dt + timedelta(days=1)

        time_to_add = duration_in_sec / SECONDS_PER_HOUR
        self.throw_if_negative(session.domain, time_to_add)

        query = select(DailyDomainSummary).where(
            DailyDomainSummary.domain_name == session.domain,
            DailyDomainSummary.gathering_date >= today_start.dt,
            DailyDomainSummary.gathering_date < tomorrow_start
        )
        self.do_addition(query, time_to_add)

    def do_addition(self, query, time_to_add):
        with self.regular_session() as db_session:
            domain: DailyDomainSummary = db_session.scalars(query).first()

            if domain is None:
                raise ImpossibleToGetHereError(
                    "Session should exist before do_addition occurs")

            # FIXME: Must test this method
            new_duration = domain.hours_spent + time_to_add

            domain.hours_spent = new_duration  # Error is here GPT
            db_session.commit()

    def throw_if_negative(self, activity, value):
        if value < 0:
            raise NegativeTimeError(activity, value)

    def shutdown(self):
        """Closes the open session without opening a new one"""
        pass

    def delete(self, id: int):
        """Delete an entry by ID"""
        with self.regular_session() as session:
            entry = session.get(DailyDomainSummary, id)
            if entry:
                session.delete(entry)
                session.commit()
            return entry
