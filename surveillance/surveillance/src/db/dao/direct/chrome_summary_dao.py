# daily_summary_dao.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import sessionmaker

import traceback
from datetime import datetime, timedelta
from typing import List

from surveillance.src.config.definitions import power_on_off_debug_file

from surveillance.src.db.models import DailyDomainSummary
from surveillance.src.util.console_logger import ConsoleLogger
from surveillance.src.object.classes import ChromeSessionData

from surveillance.src.util.dao_wrapper import validate_start_end_and_duration, validate_start_and_end_times
from surveillance.src.util.errors import SuspiciousDurationError
from surveillance.src.util.debug_util import notice_suspicious_durations, log_if_needed
from surveillance.src.util.const import SECONDS_PER_HOUR


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

    # @validate_start_end_and_duration
    # def create_if_new_else_update(self, chrome_session: ChromeSessionData, right_now: datetime):
    #     """This method doesn't use queuing since it needs to check the DB state"""
    #     target_domain_name = chrome_session.domain
        
    #     # No need to await this part
    #     # TODO: Replace .create_log with a debug table, that records every integer added to a particular log
    #     # TODO: ...the table could just be, "here's an id for a certain summary; here's the floats added to make the sum
    #     # self.chrome_logging_dao.create_log(chrome_session, right_now)

    #     # ### Calculate time difference
    #     usage_duration_in_hours = chrome_session.duration.total_seconds() / 3600

    #     existing_entry = self.read_row_for_domain(target_domain_name, right_now)
    #     print(existing_entry, "49ru")

    #     if existing_entry:                
    #         print("updating hours for " + existing_entry.domain_name)
    #         if self.debug:
    #             notice_suspicious_durations(existing_entry, chrome_session)
    #         self.logger.log_white_multiple("[chrome summary dao] adding time ",
    #                                         chrome_session.duration, " to ", target_domain_name)
    #         self.update_hours(existing_entry, usage_duration_in_hours)
    #     else:
    #         today_start = right_now.replace(
    #             hour=0, minute=0, second=0, microsecond=0)
    #         self._create(target_domain_name, usage_duration_in_hours, today_start)
    
    def start_session(self, chrome_session: ChromeSessionData, right_now):
        print("HERE 151ru")
        target_domain_name = chrome_session.domain
        
        starting_window_amt = 10  # sec
        usage_duration_in_hours =  starting_window_amt/ SECONDS_PER_HOUR

        today = right_now.replace(hour=0, minute=0, second=0,
                            microsecond=0)  # Still has tz attached
        self._create(target_domain_name, usage_duration_in_hours, today)

    def _create(self, target_domain_name, duration_in_hours, when_it_was_gathered):
        print(f"creating for {target_domain_name} with duration {duration_in_hours}, 63ru")
        with self.regular_session() as session:
            new_entry = DailyDomainSummary(
                domain_name=target_domain_name,
                hours_spent=duration_in_hours,
                gathering_date=when_it_was_gathered
            )
            session.add(new_entry)
            session.commit()

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

    def read_past_week(self, right_now: datetime):

        # +1 because weekday() counts from Monday=0
        days_since_sunday = right_now.weekday() + 1
        last_sunday = right_now - timedelta(days=days_since_sunday)
        query = select(DailyDomainSummary).where(
            func.date(DailyDomainSummary.gathering_date) >= last_sunday.date()
        )

        with self.regular_session() as session:
            result = session.execute(query)
            return result.scalars().all()

    def read_past_month(self, right_now: datetime):
        """Read all entries from the 1st of the current month through today."""
        start_of_month = right_now.replace(day=1)  # First day of current month

        query = select(DailyDomainSummary).where(
            func.date(DailyDomainSummary.gathering_date) >= start_of_month.date()
        )

        with self.regular_session() as session:
            result = session.execute(query)
            return result.scalars().all()

    def read_day(self, day: datetime) -> List[DailyDomainSummary]:
        """Read all entries for the given day."""
        today_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)
        print("read_day 113ru")
        print(today_start)
        print(tomorrow_start)

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
            existing_entry.hours_spent += usage_duration_in_hours
            
            # Commit the changes
            session.commit()


        
    def push_window_ahead_ten_sec(self, chrome_session: ChromeSessionData, right_now):
        """Finds the given session and adds ten sec to its end_time
        
        NOTE: This only ever happens after start_session
        """
        target_domain = chrome_session.domain
        today_start = right_now.replace(
            hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)

        query = select(DailyDomainSummary).where(
            DailyDomainSummary.domain_name == target_domain,
            DailyDomainSummary.gathering_date >= today_start,
            DailyDomainSummary.gathering_date < tomorrow_start
        )        
        with self.regular_session() as db_session:
            domain: DailyDomainSummary = db_session.scalars(query).first()
            # Update it if found
            if domain:
                domain.hours_spent = domain.hours_spent + 10 / SECONDS_PER_HOUR
                db_session.commit()
            else:
                # If the code got here, the summary wasn't even created yet,
                # which is likely! for the first time a program enters the program on a given day
                self.logger.log_white_multiple("INFO:", f"first time {target_domain} appears today")
                target_domain_name = chrome_session.domain
        
                # ### Calculate time difference
                if chrome_session.duration is None:
                    raise ValueError("Session duration was None")
                usage_duration_in_hours = chrome_session.duration.total_seconds() / 3600
                today = right_now.replace(hour=0, minute=0, second=0,
                                  microsecond=0)  # Still has tz attached
                self._create(target_domain_name, usage_duration_in_hours, today)
                # self.create_if_new_else_update(session, right_now)

    def deduct_remaining_duration(self, session: ChromeSessionData, duration_in_sec: int, today_start):
        """
        When a session is concluded, it was concluded partway thru the 10 sec window
        
        9 times out of 10. So we deduct the unfinished duration from its hours_spent.
        """
        target_domain = session.domain
        # today_start = right_now.replace(
        #     hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start = today_start + timedelta(days=1)

        query = select(DailyDomainSummary).where(
            DailyDomainSummary.domain_name == target_domain,
            DailyDomainSummary.gathering_date >= today_start,
            DailyDomainSummary.gathering_date < tomorrow_start
        )        
        # Update it if found
        with self.regular_session() as db_session:
            domain: DailyDomainSummary = db_session.scalars(query).first()
            # Update it if found
            if domain:
                domain.hours_spent = domain.hours_spent - duration_in_sec / SECONDS_PER_HOUR
                db_session.commit()
            else:
                # FIXME: Remove this else, it should never happen now that start_session exists here too

                # If the code got here, the summary wasn't even created yet,
                # which is likely! for the first time a program enters the program,
                # if it is cut off before the first 10 sec window elapses.
                self.logger.log_white_multiple("INFO:", f"first time {target_domain} appears today")
                self._create(target_domain, duration_in_sec / SECONDS_PER_HOUR, today_start)
                # self.create_if_new_else_update(session, session.start_time)

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
