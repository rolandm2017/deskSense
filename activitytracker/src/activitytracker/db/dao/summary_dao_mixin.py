from sqlalchemy import select, or_, text, func
from sqlalchemy.orm import DeclarativeMeta

from typing import TypeVar, Callable, Type

from datetime import timedelta, datetime

from activitytracker.config.definitions import window_push_length

from activitytracker.object.classes import ProgramSession, ChromeSession
from activitytracker.tz_handling.dao_objects import FindTodaysEntryConverter

from activitytracker.tz_handling.time_formatting import (
    attach_tz_to_obj,
    get_start_of_day_from_ult,
    get_start_of_day_from_datetime,
    attach_tz_to_all,
)
from activitytracker.util.log_dao_helper import group_logs_by_name
from activitytracker.util.errors import ImpossibleToGetHereError
from activitytracker.util.time_wrappers import UserLocalTime
from activitytracker.util.const import SECONDS_PER_HOUR
from activitytracker.util.errors import DatabaseProtectionError, NegativeTimeError


T = TypeVar("T", bound=DeclarativeMeta)

# pyright: reportAttributeAccessIssue=false


class SummaryDaoMixin:
    def _find_todays_entry(
        self,
        *,  # forces all arguments after it to be keyword-only, reducing mistakes
        session_time,
        name_filter,  # You must pass like "DailyDomainSummary.domain_name == session.domain"
        model: Type[T],
    ) -> T | None:
        if session_time is None:
            raise ValueError("start_time was not set")

        initializer = FindTodaysEntryConverter(session_time)

        query = select(model).where(
            name_filter,
            model.gathering_date >= initializer.start_of_day_with_tz,
            model.gathering_date < initializer.end_of_day_with_tz,
        )

        result = self.execute_and_read_one_or_none(query)

        if result is None:
            return None

        return attach_tz_to_obj(result, session_time.dt.tzinfo)

    def do_read_past_week(self, right_now: UserLocalTime):
        days_since_sunday = right_now.weekday() + 1
        last_sunday = right_now.dt - timedelta(days=days_since_sunday)

        query = select(self.model).where(
            func.date(self.model.gathering_date) >= last_sunday.date()
        )

        result = self.execute_and_return_all(query)
        return attach_tz_to_all(result, right_now.dt.tzinfo)

    def do_read_day(self, day: UserLocalTime):
        today_start = get_start_of_day_from_datetime(day.dt)
        tomorrow_start = today_start + timedelta(days=1)

        query = select(self.model).where(
            self.model.gathering_date >= today_start,
            self.model.gathering_date < tomorrow_start,
        )
        result = self.execute_and_return_all(query)
        return attach_tz_to_all(result, day.dt.tzinfo)

    def add_partial_window(
        self, session: ProgramSession | ChromeSession, duration_in_sec: int, name_filter
    ):
        if duration_in_sec == 0:
            return  # No work to do here
        self.throw_if_negative(session.get_name(), duration_in_sec)

        today_start: UserLocalTime = get_start_of_day_from_ult(session.start_time)
        tomorrow_start = today_start.dt + timedelta(days=1)

        time_to_add = duration_in_sec / SECONDS_PER_HOUR

        query = select(self.model).where(
            name_filter,
            self.model.gathering_date >= today_start.dt,
            self.model.gathering_date < tomorrow_start,
        )
        self.do_addition(query, time_to_add)

    def do_addition(self, query, time_to_add):
        with self.regular_session() as db_session:
            summary = db_session.scalars(query).first()

            if summary is None:
                raise ImpossibleToGetHereError(
                    "Session should exist before do_addition occurs"
                )

            # FIXME: Must test this method
            new_duration = summary.hours_spent + time_to_add

            summary.hours_spent = new_duration  # Error is here GPT
            db_session.commit()

    def execute_window_push(self, query, purpose, identifier: datetime):
        # self.logger.log_white(f"[info] looking for {purpose} with {identifier}")
        with self.regular_session() as db_session:
            # TODO: change to "Update hours"
            summary = db_session.scalars(query).first()
            # FIXME: Sometimes program | domain is None
            if summary:
                summary.hours_spent = (
                    summary.hours_spent + window_push_length / SECONDS_PER_HOUR
                )
                db_session.commit()
            else:
                raise ImpossibleToGetHereError(
                    "A summary should already exist here, but was not found: " + purpose
                )

    def _execute_read_with_restored_tz(self, query, start_time: UserLocalTime):
        result = self.execute_and_read_one_or_none(query)

        if result is None:
            return None  # Or create a default

        return attach_tz_to_obj(result, start_time.dt.tzinfo)

    def throw_if_negative(self, activity: str, value: int | float):
        if value < 0:
            raise NegativeTimeError(activity, value)

    def delete(self, id: int):
        """Delete an entry by ID"""
        with self.regular_session() as session:
            entry = session.get(self.model, id)
            if entry:
                session.delete(entry)
                session.commit()
            return entry

    def delete_all_rows(self, safety_switch=None) -> int:
        """
        Delete all rows from the table.

        Returns:
            int: The number of rows deleted
        """
        if not safety_switch:
            raise DatabaseProtectionError(
                "Cannot delete all rows without safety switch enabled. "
                "Set safety_switch=True to confirm this action."
            )

        with self.regular_session() as session:
            result = session.execute(
                # text(f"DELETE FROM daily_program_summary")
                text(f"DELETE FROM {self.table_name}")
            )
            session.commit()
            return result.rowcount
