from datetime import timedelta

from surveillance.src.util.dao_wrapper import validate_session, guarantee_start_time
from surveillance.src.util.log_dao_helper import convert_start_end_times_to_hours, convert_duration_to_hours
from surveillance.src.util.time_formatting import convert_to_utc, get_start_of_day_from_datetime, get_start_of_day_from_ult, attach_tz_to_all
from surveillance.src.util.time_wrappers import UserLocalTime

class LogTimeInitializer:
    def __init__(self, start_time: UserLocalTime) -> None:      
        self.base_start_time = convert_to_utc(start_time.get_dt_for_db())
        start_of_day = get_start_of_day_from_datetime(start_time.get_dt_for_db())
        self.start_of_day_as_utc = convert_to_utc(start_of_day)
        self.start_window_end = self.base_start_time + timedelta(seconds=10)