"""
Asserts that:

1. Conversion from UTC to <tz> works.
"""
import pytest

from datetime import datetime, timezone
import pytz

from surveillance.src.db.models import ProgramSummaryLog, DailyProgramSummary
from surveillance.src.tz_handling.time_formatting import convert_to_utc, convert_to_timezone, convert_summary_to_tz, convert_log_to_tz

tokyo_tz = pytz.timezone("Asia/Tokyo")  # UTC +9
pst_tz = pytz.timezone("America/Los_Angeles")  # UTC -7

utc_tz = pytz.timezone("UTC")


def test_setup_conditions():
    midday = 12
    some_tokyo_time = tokyo_tz.localize(
        datetime(2025, 4, 15, midday + 9, 40, 0))
    some_pst_time = pst_tz.localize(datetime(2025, 4, 15, midday - 7, 40, 0))

    tokyo_as_utc = some_tokyo_time.replace(hour=midday)
    pst_as_utc = some_pst_time.replace(hour=midday)

    manual_conversion_works = tokyo_as_utc.hour == midday and pst_as_utc.hour == midday
    assert manual_conversion_works


def test_convert_to_utc():
    """
    Show that the start state {some_hour, non-UTC timezone} comes out as { some hour - offset, UTC timezone}
    """
    midday = 12

    # Tokyo is UTC +9
    # PST is UTC -7

    tokyo_hour = midday + 9
    some_tokyo_time = tokyo_tz.localize(
        datetime(2025, 4, 15, tokyo_hour, 40, 0))

    pst_hour = midday - 7
    some_pst_time = pst_tz.localize(datetime(2025, 4, 15, pst_hour, 40, 0))

    tokyo = convert_to_utc(some_tokyo_time)
    pst = convert_to_utc(some_pst_time)

    assert tokyo.tzinfo == timezone.utc
    assert tokyo.hour == midday

    assert pst.tzinfo == timezone.utc
    assert pst.hour == midday


def test_convert_to_timezone():
    midday = 12
    some_utc_time = utc_tz.localize(datetime(2025, 4, 15, midday, 40, 0))

    asia_target = "Asia/Tokyo"
    tokyo_from_utc = convert_to_timezone(some_utc_time, asia_target)

    pst_target = "America/Los_Angeles"
    pst_from_utc = convert_to_timezone(some_utc_time, pst_target)

    assert str(tokyo_from_utc.tzinfo) == asia_target
    assert tokyo_from_utc.hour == midday + 9

    assert str(pst_from_utc.tzinfo) == pst_target
    assert pst_from_utc.hour == midday - 7


def test_convert_summary_back_to_tz():
    pst_target = "America/Los_Angeles"
    pst_offset = -7

    t0 = utc_tz.localize(datetime(2025, 3, 23, 9, 25, 31))

    mock_db_result = DailyProgramSummary()
    mock_db_result.program_name = "readDayTest"
    mock_db_result.gathering_date = t0

    convert_summary_to_tz(mock_db_result, pst_tz)

    # assert the time is now adjusted for the offset: hours = hours + offset
    assert mock_db_result.gathering_date.hour == t0.hour + pst_offset
    assert str(mock_db_result.gathering_date.tzinfo) == pst_target


tokyo_tz = pytz.timezone("Asia/Tokyo")  # UTC +9
pst_tz = pytz.timezone("America/Los_Angeles")  # UTC -7

utc_tz = pytz.timezone("UTC")


def test_convert_log_back_to_target_tz():
    asia_target = "Asia/Tokyo"
    tokyo_offset = 9

    expected_target_tz_hour = 21

    t0 = utc_tz.localize(datetime(2025, 1, 20, 12, 25, 0))
    t1 = utc_tz.localize(datetime(2025, 1, 20, 12, 30, 0))
    # Test setup:
    assert t0.hour == 12
    assert t1.hour == 12

    t2 = utc_tz.localize(datetime(2025, 1, 20, 0, 0, 0))

    mock_db_result = ProgramSummaryLog()
    mock_db_result.start_time = t0
    mock_db_result.end_time = t1
    mock_db_result.gathering_date = t2

    convert_log_to_tz(mock_db_result, tokyo_tz)

    # assert the time is now adjusted for the offset: hours = hours + offset
    assert mock_db_result.start_time.hour == 21  # 12 + 9
    assert mock_db_result.end_time.hour == 21
    assert mock_db_result.gathering_date.hour == t2.hour + tokyo_offset
    assert str(mock_db_result.gathering_date.tzinfo) == asia_target
