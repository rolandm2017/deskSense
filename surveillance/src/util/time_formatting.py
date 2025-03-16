from datetime import datetime, timedelta
import pytz

from typing import List, cast

from ..db.models import TimelineEntryObj

from ..config.definitions import local_time_zone, daylight_savings_tz_offset


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
