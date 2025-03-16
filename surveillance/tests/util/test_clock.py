import pytest
from unittest.mock import patch

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


from src.services.services import TimezoneService

from src.config.definitions import local_time_zone, regular_tz_offset, daylight_savings_tz_offset
from src.object.pydantic_dto import TabChangeEvent
from src.util.clock import UserFacingClock

user_facing_clock = UserFacingClock()


def test_now_has_tz():
    now = user_facing_clock.now()

    assert isinstance(now, datetime)

    assert str(now.tzinfo) == local_time_zone

    offset = now.utcoffset()
    assert hasattr(offset, "total_seconds") and offset is not None
    offset_hours = int(offset.total_seconds() / 3600)

    assert offset_hours in [regular_tz_offset, daylight_savings_tz_offset]


def test_seconds_have_elapsed():
    earlier = datetime.now()
    later = earlier + timedelta(seconds=11)

    assert not user_facing_clock.seconds_have_elapsed(
        later, earlier, 12), "The 'less than' condition failed"
    assert user_facing_clock.seconds_have_elapsed(
        later, earlier, 11), "The boundary failed"
    assert user_facing_clock.seconds_have_elapsed(
        later, earlier, 10), "The 'greater than' condition failed"


def test_seconds_have_elapsed_sad_path():
    today = datetime.now()
    tomorrow = today + timedelta(days=1)

    with pytest.raises(ValueError, match="current_time must be later than previous_time."):
        user_facing_clock.seconds_have_elapsed(today, tomorrow, 10)


def test_get_previous_sunday():
    user_facing_clock_local = UserFacingClock()

    # ### It works with an argument
    feb_26_2025_dt = datetime(2025, 2, 26)  # A Wednesday.

    a_sunday = user_facing_clock_local.get_previous_sunday(feb_26_2025_dt)

    sunday_in_datetime = 6

    assert a_sunday.weekday() == sunday_in_datetime
    assert a_sunday.day == 26 - 3  # Wed, Tues, Mon, Sun == 0, 1, 2, 3
    # ### It works without an argument
    # Arrange: Rig clock.now() to return a very specific date, to enable testing.
    the_11th_a_tuesday = 11

    # A Tuesday.
    test_now = datetime(2025, 3, the_11th_a_tuesday, tzinfo=ZoneInfo("UTC"))

    with patch.object(UserFacingClock, "now", return_value=test_now):
        some_sunday = user_facing_clock_local.get_previous_sunday()

        assert some_sunday.weekday() == sunday_in_datetime
        assert some_sunday.day == the_11th_a_tuesday - 2


def test_get_day_start():
    early = datetime(2025, 1, 29, 4, 4, 4)
    midday = datetime(2025, 2, 26, 12, 3, 3)
    quite_late = datetime(2025, 3, 11, 23, 31, 31)

    s1 = user_facing_clock.get_day_start(early)
    s2 = user_facing_clock.get_day_start(midday)
    s3 = user_facing_clock.get_day_start(quite_late)

    assert s1.day == early.day
    assert s2.day == midday.day
    assert s3.day == quite_late.day

    assert s1.hour == 0 and s1.minute == 0
    assert s2.hour == 0 and s2.minute == 0
    assert s3.hour == 0 and s3.minute == 0


def test_is_timezone_aware():
    naive_dt = datetime.now()  # TODO: Make them actually like, correct.
    naive_dt_2 = naive_dt + timedelta(seconds=9)

    # With UTC timezone info    tz_aware_dt = datetime.now()
    aware_dt = datetime.now(ZoneInfo("EST"))
    aware_dt_2 = aware_dt + timedelta(seconds=5)

    assert user_facing_clock.is_timezone_aware(aware_dt)
    assert user_facing_clock.is_timezone_aware(aware_dt_2)
    assert not user_facing_clock.is_timezone_aware(naive_dt)
    assert not user_facing_clock.is_timezone_aware(naive_dt_2)


def test_timezones_are_same():
    aware_dt = datetime.now(ZoneInfo("EST"))
    aware_dt_2 = aware_dt + timedelta(seconds=5)

    another = datetime.now(ZoneInfo("Europe/Berlin"))
    another_v2 = another - timedelta(hours=3)

    assert user_facing_clock.timezones_are_same(aware_dt, aware_dt_2)
    assert user_facing_clock.timezones_are_same(another, another_v2)
    assert not user_facing_clock.timezones_are_same(
        aware_dt, another), "Different TZ datetimes failed detection"
