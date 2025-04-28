from datetime import datetime, timedelta, timezone
import pytz

from typing import List, cast

from surveillance.src.db.models import TimelineEntryObj

from surveillance.src.config.definitions import local_time_zone, daylight_savings_tz_offset
from surveillance.src.util.time_wrappers import UserLocalTime
from surveillance.src.util.errors import TimezoneUnawareError



def convert_to_utc(dt: datetime):
    return dt.astimezone(timezone.utc)

def require_tzinfo(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        raise TimezoneUnawareError("require_tzinfo", dt)
    return dt

# Alternate method for below code
# def get_start_of_day(dt):
#     """Get the start of the day (midnight) for the given datetime"""
#     return datetime(dt.year, dt.month, dt.day, tzinfo=dt.tzinfo)

def get_start_of_day_from_ult(ult: UserLocalTime):
    return UserLocalTime(ult.dt.replace(hour=0, minute=0, second=0, microsecond=0))

def get_start_of_day_from_datetime(dt: datetime):
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)

def get_start_of_day(some_time_obj: datetime | UserLocalTime):
    """If you put in March 3 3:00 PM PST, you will get out march 3 12:00 AM *PST*! """
    # Timezone stays attached.
    if isinstance(some_time_obj, UserLocalTime):
        return UserLocalTime(some_time_obj.dt.replace(hour=0, minute=0, second=0, microsecond=0))
    return some_time_obj.replace(hour=0, minute=0, second=0, microsecond=0)


def account_for_timezone_offset(dt, users_local_tz_offset):

    return dt + timedelta(hours=users_local_tz_offset)


def convert_to_timezone(dt, timezone_str):
    """
    Convert a datetime to the specified timezone.

    Parameters:
    - dt: The datetime object to convert
    - timezone_str: String representing the timezone (e.g., 'America/Los_Angeles', 'US/Eastern', 'Europe/London')

    Returns:
    - A datetime object in the specified timezone
    """
    # Ensure the datetime is timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)  # Assume UTC if not specified

    # Convert to the target timezone
    target_tz = pytz.timezone(timezone_str)
    with_updated_tz = dt.astimezone(target_tz)
    # with_updated_time = account_for_timezone_offset(
    #     with_updated_tz, daylight_savings_tz_offset)
    # return with_updated_time
    return with_updated_tz


def format_for_local_time(events: List[TimelineEntryObj]) -> List[TimelineEntryObj]:
    formatted_entries = []

    for event in events:
        # Create a copy or modify in-place as needed
        entry_copy = event  # or make a deep copy if needed

        start_value = cast(datetime, entry_copy.start)
        if start_value:
            entry_copy.start = convert_to_timezone(  # type: ignore
                start_value, local_time_zone)

        end_value = cast(datetime, entry_copy.end)
        if end_value:
            entry_copy.end = convert_to_timezone(  # type: ignore
                end_value, local_time_zone)

        formatted_entries.append(entry_copy)

    return formatted_entries

def parse_time_string(time_str):
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds_parts = parts[2].split('.')
        seconds = int(seconds_parts[0])
        microseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0

        return timedelta(
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            microseconds=microseconds
        )