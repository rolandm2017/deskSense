from sqlalchemy import or_, select
from sqlalchemy.orm import DeclarativeMeta

from datetime import timedelta

from typing import Callable, Type, TypeVar

from activitytracker.db.models import (
    DomainSummaryLog,
    ProgramSummaryLog,
    VideoSummaryLog,
)
from activitytracker.tz_handling.time_formatting import (
    attach_tz_to_all,
    convert_to_utc,
    get_start_of_day_from_datetime,
    get_start_of_day_from_ult,
)
from activitytracker.util.errors import ImpossibleToGetHereError
from activitytracker.util.log_dao_helper import group_logs_by_name
from activitytracker.util.time_wrappers import UserLocalTime

T = TypeVar("T", bound=DeclarativeMeta)

# pyright: reportAttributeAccessIssue=false


class LoggingDaoMixin:
    def _read_day_as_sorted(
        self, day: UserLocalTime, model: Type[T], sort_column
    ) -> dict[str, T]:
        start_of_day = get_start_of_day_from_datetime(day.get_dt_for_db())
        start_of_day = convert_to_utc(start_of_day)
        end_of_day = start_of_day + timedelta(days=1)

        query = (
            select(model)
            .where(model.gathering_date >= start_of_day, model.gathering_date < end_of_day)
            .order_by(sort_column)
        )

        logs = self.execute_and_return_all(query)
        logs = attach_tz_to_all(logs, day.dt.tzinfo)
        grouped_logs = group_logs_by_name(logs)

        return grouped_logs

    def attach_final_values_and_update(
        self, session, log: ProgramSummaryLog | DomainSummaryLog | VideoSummaryLog
    ):
        finalized_duration = (session.end_time.dt - session.start_time.dt).total_seconds()
        if finalized_duration < 0:

            print("session:", session)
            print("log", log)
            raise ImpossibleToGetHereError("A negative duration is impossible")
        discovered_final_val = convert_to_utc(session.end_time.get_dt_for_db())

        # Replace whatever used to be there
        log.duration_in_sec = finalized_duration
        log.end_time = discovered_final_val
        log.end_time_local = session.end_time.dt
        self.update_item(log)

    def do_read_last_24_hrs(self, right_now: UserLocalTime):
        """Fetch all program log entries from the last 24 hours

        NOTE: the database is storing and returning times in UTC
        """
        cutoff_time = right_now.dt - timedelta(hours=24)
        query = (
            select(self.model)
            .where(self.model.created_at >= cutoff_time)
            .order_by(self.model.created_at.desc())
        )
        results = self.execute_and_return_all(query)
        return attach_tz_to_all(results, right_now.dt.tzinfo)

    def find_orphans(self, latest_shutdown_time, startup_time):
        """
        Finds orphaned sessions that:
        1. Started before shutdown but never ended (end_time is None)
        2. Started before shutdown but ended after next startup (impossible)

        Args:
            latest_shutdown_time: Timestamp when system shut down
            startup_time: Timestamp when system started up again
        """
        query = (
            select(self.model)
            .where(
                # Started before shutdown
                self.model.start_time <= latest_shutdown_time,
                # AND (end_time is None OR end_time is after next startup)
                or_(
                    self.model.end_time == None,  # Sessions never closed
                    self.model.end_time >= startup_time,  # End time after startup
                ),
            )
            .order_by(self.model.start_time)
        )
        # the database is storing and returning times in UTC
        return self.execute_and_return_all(query)

    def find_phantoms(self, latest_shutdown_time, startup_time):
        """
        Finds phantom sessions that impossibly started while the system was off.

        Args:
            latest_shutdown_time: Timestamp when system shut down
            startup_time: Timestamp when system started up again
        """
        query = (
            select(self.model)
            .where(
                # Started after shutdown
                self.model.start_time > latest_shutdown_time,
                # But before startup
                self.model.start_time < startup_time,
            )
            .order_by(self.model.start_time)
        )
        # the database is storing and returning times in UTC
        return self.execute_and_return_all(query)
