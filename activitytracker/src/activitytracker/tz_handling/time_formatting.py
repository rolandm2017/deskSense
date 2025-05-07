import pytz
from datetime import datetime, timedelta, timezone

from typing import List, cast

from activitytracker.config.definitions import (
    daylight_savings_tz_offset,
    local_time_zone,
)
from activitytracker.db.models import (
    DailySummaryBase,
    SummaryLogBase,
    SystemStatus,
    TimelineEntryObj,
)
from activitytracker.util.errors import TimezoneUnawareError
from activitytracker.util.time_wrappers import UserLocalTime


def convert_all_to_tz(obj_list, target_tz):
    # Func assumes the obj list will all be of the same type
    if isinstance(obj_list[0], DailySummaryBase):
        # The gathering date is either the same day, or the previous day.
        # 00:00:00-04:00 -> 20:00:00 UTC -1 day.
        # The hours reveal the original tz. 19:00:00 -> UTC -5
        for obj in obj_list:
            convert_summary_to_tz(obj, target_tz)
        return obj_list
    elif isinstance(obj_list[0], SummaryLogBase):
        for log_obj in obj_list:
            # FIXME: If _local fields are None, convert the gathering_date
            convert_log_to_tz(log_obj, target_tz)
        return obj_list
    else:
        raise NotImplementedError("Summaries and Logs are converted so far")


def convert_summary_to_tz(summary_obj: DailySummaryBase, tz):
    """
    Modifies the object in place! Mutates the reference.
    """
    utc = pytz.UTC

    # Check if gathering_date already has timezone info
    if summary_obj.gathering_date.tzinfo is None:
        # If naive, localize to UTC first
        utc_time = utc.localize(summary_obj.gathering_date)
    else:
        # If already has timezone info, just use it
        utc_time = summary_obj.gathering_date

    converted_time = utc_time.astimezone(tz)

    summary_obj.gathering_date = converted_time


def convert_log_to_tz(log_obj: SummaryLogBase, tz):
    """
    Modifies the object in place! Mutates the reference.
    """
    # For local times (timezone=False in your model)
    # First, determine the original timezone (if known)
    original_tz = pytz.timezone("UTC")  # Assuming they were originally UTC

    # Properly localize and then convert each datetime
    if log_obj.gathering_date.tzinfo is None:
        temp_time = original_tz.localize(log_obj.gathering_date)
        log_obj.gathering_date = temp_time.astimezone(tz)
    elif (
        log_obj.gathering_date.tzinfo == timezone.utc
        or str(log_obj.gathering_date.tzinfo) == "UTC"
    ):
        # Already UTC-aware - just convert to target timezone
        log_obj.gathering_date = log_obj.gathering_date.astimezone(tz)

    if log_obj.start_time.tzinfo is None:
        temp_time = original_tz.localize(log_obj.start_time)
        log_obj.start_time = temp_time.astimezone(tz)
    elif log_obj.start_time.tzinfo == timezone.utc or str(log_obj.start_time.tzinfo) == "UTC":
        # Already UTC-aware - just convert to target timezone
        log_obj.start_time = log_obj.start_time.astimezone(tz)

    if log_obj.end_time.tzinfo is None:
        temp_time = original_tz.localize(log_obj.end_time)
        log_obj.end_time = temp_time.astimezone(tz)
    elif log_obj.end_time.tzinfo == timezone.utc or str(log_obj.end_time.tzinfo) == "UTC":
        # Already UTC-aware - just convert to target timezone
        log_obj.end_time = log_obj.end_time.astimezone(tz)


def attach_tz_to_obj(obj, target_tz):
    """Used to attach tz info after DAOs read data"""
    # Func assumes the obj will be of a specific type
    if isinstance(obj, DailySummaryBase):
        # The gathering date is either the same day, or the previous day.
        # 00:00:00-04:00 -> 20:00:00 UTC -1 day.
        # The hours reveal the original tz. 19:00:00 -> UTC -5
        # FIXME: If _local fields are None, convert the gathering_date
        attach_tz_to_local_fields_for_summary(obj, target_tz)

        return obj
    elif isinstance(obj, SummaryLogBase):
        # Properly assign the new datetime objects back to the attributes
        # FIXME: If _local fields are None, convert the gathering_date
        attach_tz_to_local_fields_for_logs(obj, target_tz)
        return obj
    else:
        raise NotImplementedError("Summaries and Logs are converted so far")


def attach_tz_to_all(obj_list, target_tz):
    """Used to attach tz info after DAOs read data"""
    if not obj_list:
        return obj_list  # Return empty list if input is empty
    # Func assumes the obj list will all be of the same type
    if isinstance(obj_list[0], DailySummaryBase):
        # The gathering date is either the same day, or the previous day.
        # 00:00:00-04:00 -> 20:00:00 UTC -1 day.
        # The hours reveal the original tz. 19:00:00 -> UTC -5
        for obj in obj_list:
            attach_tz_to_local_fields_for_summary(obj, target_tz)
        return obj_list
    elif isinstance(obj_list[0], SummaryLogBase):
        for log_obj in obj_list:
            # FIXME: If _local fields are None, convert the gathering_date
            attach_tz_to_local_fields_for_logs(log_obj, target_tz)
        return obj_list
    elif isinstance(obj_list[0], SystemStatus):
        for status in obj_list:
            attach_tz_to_created_at_field_for_status(status, target_tz)
    else:
        raise NotImplementedError("Summaries and Logs are converted so far")


def attach_tz_to_created_at_field_for_status(status: SystemStatus, tz):
    status.created_at = status.created_at.replace(tzinfo=tz)


def attach_tz_to_local_fields_for_summary(summary_obj: DailySummaryBase, tz):
    summary_obj.gathering_date_local = summary_obj.gathering_date_local.replace(tzinfo=tz)


def attach_tz_to_local_fields_for_logs(log_obj: SummaryLogBase, tz):
    log_obj.gathering_date_local = log_obj.gathering_date_local.replace(tzinfo=tz)
    log_obj.start_time_local = log_obj.start_time_local.replace(tzinfo=tz)
    log_obj.end_time_local = log_obj.end_time_local.replace(tzinfo=tz)


def convert_to_utc(dt: datetime):
    """
    Convert a timezone-aware datetime to UTC.

    This preserves the absolute moment in time but changes the representation
    to UTC timezone, adjusting the hour value accordingly.

    Parameters:
    - dt: The datetime object to convert (must be timezone-aware)

    Returns:
    - A datetime object representing the same moment in UTC

    So 9 pm Asia/Tokyo will be returned as 12 pm UTC.
    """
    if dt.tzinfo is None:
        raise ValueError("Input datetime must be timezone-aware")
    # preserves the absolute moment in time while changing the timezone representation
    return dt.astimezone(timezone.utc)


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


def account_for_timezone_offset(dt, users_local_tz_offset):

    return dt + timedelta(hours=users_local_tz_offset)


def format_for_local_time(events: List[TimelineEntryObj]) -> List[TimelineEntryObj]:
    formatted_entries = []

    for event in events:
        # Create a copy or modify in-place as needed
        entry_copy = event  # or make a deep copy if needed

        start_value = cast(datetime, entry_copy.start)
        if start_value:
            entry_copy.start = convert_to_timezone(start_value, local_time_zone)  # type: ignore

        end_value = cast(datetime, entry_copy.end)
        if end_value:
            entry_copy.end = convert_to_timezone(end_value, local_time_zone)  # type: ignore

        formatted_entries.append(entry_copy)

    return formatted_entries


def parse_time_string(time_str):
    parts = time_str.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds_parts = parts[2].split(".")
    seconds = int(seconds_parts[0])
    microseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0

    return timedelta(hours=hours, minutes=minutes, seconds=seconds, microseconds=microseconds)
