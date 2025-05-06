from datetime import timedelta, datetime, time

from surveillance.util.log_dao_helper import convert_start_end_times_to_hours, convert_duration_to_hours
from surveillance.tz_handling.time_formatting import (
    convert_to_utc,
    get_start_of_day_from_ult, attach_tz_to_all,
    get_start_of_day_from_datetime)
from surveillance.util.time_wrappers import UserLocalTime


class LogTimeConverter:
    def __init__(self, start_time: UserLocalTime) -> None:
        start_time_as_utc = convert_to_utc(start_time.dt)
        self.base_start_time_as_utc = start_time_as_utc

        self.base_start_window_end = start_time_as_utc + timedelta(seconds=10)

        start_of_day = get_start_of_day_from_datetime(start_time.dt)

        self.start_of_day_as_utc = convert_to_utc(start_of_day)


class FindTodaysEntryConverter:
    def __init__(self, session_start_time: UserLocalTime) -> None:
        if session_start_time is None:
            raise ValueError("start_time was not set")

        date_for_day = get_start_of_day_from_datetime(session_start_time.dt)

        self.start_of_day_with_tz = datetime.combine(
            date_for_day, time.min, tzinfo=date_for_day.tzinfo)
        self.end_of_day_with_tz = datetime.combine(
            date_for_day, time.max, tzinfo=date_for_day.tzinfo)
