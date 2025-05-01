from sqlalchemy import select, or_
from sqlalchemy.orm import DeclarativeMeta

from typing import TypeVar, Callable, Type

from datetime import timedelta

from surveillance.src.db.models import DomainSummaryLog, ProgramSummaryLog

from surveillance.src.util.time_formatting import convert_to_utc, get_start_of_day_from_datetime, get_start_of_day_from_ult, attach_tz_to_all
from surveillance.src.util.log_dao_helper import group_logs_by_name
from surveillance.src.util.errors import ImpossibleToGetHereError
from surveillance.src.util.time_wrappers import UserLocalTime


T = TypeVar('T', bound=DeclarativeMeta)

# pyright: reportAttributeAccessIssue=false

class LoggingDaoMixin:

    def attach_final_values_and_update(self, session, log):
        finalized_duration = (session.end_time.dt - session.start_time.dt).total_seconds()        
        if finalized_duration < 0:
            raise ImpossibleToGetHereError("A negative duration is impossible")
        discovered_final_val = convert_to_utc(session.end_time.get_dt_for_db()).replace(tzinfo=None)

        # Replace whatever used to be there
        log.duration_in_sec = finalized_duration
        log.end_time = discovered_final_val
        log.end_time_local = session.end_time.dt
        self.update_item(log)

    def _read_day_as_sorted(
        self,
        day: UserLocalTime,
        model: Type[T],
        sort_column
    ) -> dict[str, T]:
        start_of_day = get_start_of_day_from_datetime(day.get_dt_for_db())
        start_of_day = convert_to_utc(start_of_day)
        end_of_day = start_of_day + timedelta(days=1)

        self.logger.log_white(f"INFO: querying start_of_day: {start_of_day}\n\tto end_of_day: {end_of_day}")

        query = select(model).where(
            model.gathering_date >= start_of_day,
            model.gathering_date < end_of_day
        ).order_by(sort_column)

        logs = self.execute_and_return_all(query)
        logs = attach_tz_to_all(logs, day.dt.tzinfo)
        grouped_logs = group_logs_by_name(logs)

        return grouped_logs
