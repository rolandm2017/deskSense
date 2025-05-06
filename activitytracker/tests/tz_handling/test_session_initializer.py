"""
Asserts that:

1. DAO start_session converters do what they say.
"""
import pytest

from datetime import datetime

import pytz

# TODO
from activitytracker.tz_handling.dao_objects import LogTimeConverter, FindTodaysEntryConverter
from activitytracker.util.time_wrappers import UserLocalTime

from activitytracker.tz_handling.time_formatting import convert_to_utc


def test_log_time_converter():
    tokyo_tz_str = "Asia/Tokyo"  # UTC +9
    tokyo_tz = pytz.timezone(tokyo_tz_str)

    tokyo_offset = 9

    t0 = datetime(2025, 5, 3, 11, 26, 0)
    midday_in_asia = tokyo_tz.localize(t0)

    # Test setup conditions
    assert str(midday_in_asia.tzinfo) == tokyo_tz_str

    some_ult = UserLocalTime(midday_in_asia)

    start_of_day = midday_in_asia.replace(hour=0)
    start_of_tokyo_day_in_utc = start_of_day.hour - tokyo_offset

    converter = LogTimeConverter(some_ult)

    assert str(converter.base_start_time_as_utc.tzinfo) == "UTC"
    assert str(converter.base_start_window_end.tzinfo) == "UTC"

    hour_was_converted_to_utc = converter.base_start_time_as_utc.hour == midday_in_asia.hour - tokyo_offset
    assert hour_was_converted_to_utc
    assert converter.base_start_time_as_utc.minute == midday_in_asia.minute

    hour_was_converted_to_utc = converter.base_start_window_end.hour == midday_in_asia.hour - tokyo_offset
    assert hour_was_converted_to_utc
    assert converter.base_start_window_end.second == midday_in_asia.second + 10

    assert converter.start_of_day_as_utc.hour == start_of_tokyo_day_in_utc % 24
    assert converter.start_of_day_as_utc.day == midday_in_asia.day - 1


def test_find_todays_entry_converter():
    pst_tz_str = "America/Los_Angeles"  # UTC +9
    pst_tz = pytz.timezone(pst_tz_str)

    pst_offset = 7

    t0 = datetime(2025, 5, 3, 11, 26, 0)
    midday_in_asia = pst_tz.localize(t0)

    # Test setup conditions
    assert str(midday_in_asia.tzinfo) == pst_tz_str

    some_ult = UserLocalTime(midday_in_asia)

    converter = FindTodaysEntryConverter(some_ult)

    assert str(converter.start_of_day_with_tz.tzinfo) == pst_tz_str
    assert str(converter.end_of_day_with_tz.tzinfo) == pst_tz_str
    assert converter.start_of_day_with_tz.hour == 0
    assert converter.end_of_day_with_tz.hour == 23
    assert converter.end_of_day_with_tz.minute == 59
