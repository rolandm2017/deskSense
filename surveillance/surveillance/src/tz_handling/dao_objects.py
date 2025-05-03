from datetime import timedelta, datetime, time

from surveillance.src.util.dao_wrapper import validate_session, guarantee_start_time
from surveillance.src.util.log_dao_helper import convert_start_end_times_to_hours, convert_duration_to_hours
from surveillance.surveillance.src.tz_handling.time_formatting import (
    convert_to_utc,
    get_start_of_day_from_ult, attach_tz_to_all,
    get_start_of_day_from_datetime)
from surveillance.src.util.time_wrappers import UserLocalTime


class LogTimeInitializer:
    def __init__(self, start_time: UserLocalTime) -> None:
        self.base_start_time = convert_to_utc(
            start_time.get_dt_for_db())
        start_of_day = get_start_of_day_from_datetime(
            start_time.get_dt_for_db())
        self.start_of_day_as_utc = convert_to_utc(start_of_day)
        self.start_window_end = self.base_start_time + timedelta(seconds=10)


class FindTodaysEntryInitializer:
    def __init__(self, session_start_time: UserLocalTime) -> None:
        if session_start_time is None:
            raise ValueError("start_time was not set")
        date_for_day = get_start_of_day_from_datetime(session_start_time.dt)
        self.start_of_day_with_tz = datetime.combine(
            date_for_day, time.min, tzinfo=date_for_day.tzinfo)
        self.end_of_day_with_tz = datetime.combine(
            date_for_day, time.max, tzinfo=date_for_day.tzinfo)
