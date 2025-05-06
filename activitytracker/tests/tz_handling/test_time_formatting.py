
import pytest
from unittest.mock import patch

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


from activitytracker.tz_handling.time_formatting import account_for_timezone_offset, convert_to_timezone, format_for_local_time


def test_account_for_timezone_offset():
    offset = 3
    start_hour = 13
    some_time = datetime(2025, 3, 15, start_hour, 1, 1)

    accounted_for = account_for_timezone_offset(some_time, offset)
    assert accounted_for.hour == start_hour + offset
    assert accounted_for.minute == some_time.minute

    # It also works with negative offset

    offset = -4
    start_hour = 13
    some_time = datetime(2025, 3, 15, start_hour, 1, 1)

    accounted_for = account_for_timezone_offset(some_time, offset)
    assert accounted_for.hour == start_hour + offset
    assert accounted_for.minute == some_time.minute


class TestConvertToTimezone:
    """Group tests for convert_to_timezone function."""

    def test_regular_inputs(self):

        # EST (Eastern Standard Time) - UTC -5 hours
        # March 15, 2025 at 14:30:00
        est_dt = datetime(2025, 3, 15, 14, 30, 0, 0)
        # Localize to EST (New York is in EST)
        est_dt = est_dt.replace(tzinfo=ZoneInfo("America/New_York"))

        # Europe/Berlin - UTC +1 (standard time) or UTC +2 (daylight saving time, depending on the time of year)
        # March 15, 2025 at 14:30:00
        berlin_dt = datetime(2025, 3, 15, 14, 30, 0, 0)
        berlin_dt = berlin_dt.replace(tzinfo=ZoneInfo(
            "Europe/Berlin"))  # Localize to Europe/Berlin

        # ###
        # ### Test setup circumstances
        # ###
        # Assertions
        assert est_dt.tzinfo == ZoneInfo(
            "America/New_York"), f"Expected America/New_York, but got {est_dt.tzinfo}"
        assert berlin_dt.tzinfo == ZoneInfo(
            "Europe/Berlin"), f"Expected Europe/Berlin, but got {berlin_dt.tzinfo}"

        # Checking the expected UTC offsets (in hours)
        est_utc_offset = est_dt.utcoffset()
        assert est_utc_offset is not None
        assert est_utc_offset.total_seconds() == -4 * \
            3600, f"Expected UTC offset -4 hours, but got {est_utc_offset}"

        # For Berlin, we keep the check for +1 hour or +2 hours depending on daylight saving time
        berlin_utc_offset = berlin_dt.utcoffset()
        assert berlin_utc_offset is not None
        assert berlin_utc_offset.total_seconds(
        ) == 1 * 3600, f"Expected UTC offset +1 hour, but got {berlin_utc_offset}"

        # Verifying the datetime values
        assert est_dt.year == 2025, f"Expected year 2025, but got {est_dt.year}"
        assert est_dt.month == 3, f"Expected month 3, but got {est_dt.month}"
        assert est_dt.day == 15, f"Expected day 15, but got {est_dt.day}"
        assert est_dt.hour == 14, f"Expected hour 14, but got {est_dt.hour}"
        assert est_dt.minute == 30, f"Expected minute 30, but got {est_dt.minute}"

        assert berlin_dt.year == 2025, f"Expected year 2025, but got {berlin_dt.year}"
        assert berlin_dt.month == 3, f"Expected month 3, but got {berlin_dt.month}"
        assert berlin_dt.day == 15, f"Expected day 15, but got {berlin_dt.day}"
        assert berlin_dt.hour == 14, f"Expected hour 14, but got {berlin_dt.hour}"
        assert berlin_dt.minute == 30, f"Expected minute 30, but got {berlin_dt.minute}"
        # #
        # ### DONE verifying setup circumstances
        # #

        dt = datetime.now()

        hawaii_time = convert_to_timezone(dt, "Pacific/Honolulu")  # -10
        european_time = convert_to_timezone(dt, 'Europe/London')  # 0 or 1
        east_asian_time = convert_to_timezone(dt, 'Asia/Tokyo')  # 9
        south_american_time = convert_to_timezone(
            dt, 'America/Sao_Paulo')  # -3

        hawaii_offset = -10
        european_offset = 0
        european_offset_daylight_savings = 1
        east_asian_offset = 9
        south_american_offset = -3

        assert (dt.hour + hawaii_offset) % 24 == hawaii_time.hour
        assert (dt.hour + european_offset) % 24 == european_time.hour or (
            dt.hour + european_offset_daylight_savings) % 24 == european_time.hour
        assert (dt.hour + east_asian_offset) % 24 == east_asian_time.hour
        assert (dt.hour + south_american_offset) % 24 == south_american_time.hour

    def test_when_no_tz_present(self):
        no_tz = datetime.now()  # does not have a tz

        hawaii_time = convert_to_timezone(no_tz, "Pacific/Honolulu")  # -10
        european_time = convert_to_timezone(no_tz, 'Europe/London')  # 0 or 1
        east_asian_time = convert_to_timezone(no_tz, 'Asia/Tokyo')  # 9
        south_american_time = convert_to_timezone(
            no_tz, 'America/Sao_Paulo')  # -3

        hawaii_offset = -10
        european_offset = 0
        european_offset_daylight_savings = 1
        east_asian_offset = 9
        south_american_offset = -3

        assert (no_tz.hour + hawaii_offset) % 24 == hawaii_time.hour
        assert (no_tz.hour + european_offset) % 24 == european_time.hour or (
            no_tz.hour + european_offset_daylight_savings) % 24 == european_time.hour
        assert (no_tz.hour + east_asian_offset) % 24 == east_asian_time.hour
        assert (no_tz.hour + south_american_offset) % 24 == south_american_time.hour


class FormatForLocalTime:
    def test_typical_list_of_inputs(self):
        pass

    def test_already_all_the_right_time(self):
        pass
