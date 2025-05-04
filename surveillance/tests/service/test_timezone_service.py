import pytest

from datetime import datetime

from surveillance.src.services.tiny_services import TimezoneService

from surveillance.src.config.definitions import local_time_zone, regular_tz_offset, daylight_savings_tz_offset
from surveillance.src.object.pydantic_dto import UtcDtTabChange

timezone_service = TimezoneService()


def test_get_user_timezone():
    tz_for_user = timezone_service.get_tz_for_user(
        "whatever for now")
    assert tz_for_user == local_time_zone


def test_localize_dt_to_user_tz():
    some_dt = datetime(2025, 4, 15, 15, 15, 15)
    localized = timezone_service.localize_to_user_tz(some_dt)

    assert localized.tzinfo is not None
    assert str(localized.tzinfo) == local_time_zone
    assert localized.hour == some_dt.hour
    assert localized.minute == some_dt.minute


def test_convert_tab_change_timezone():
    tab_title = "World's Best Foo"
    url = "foo.com"
    start_time = datetime.now()
    some_tab_change_event = UtcDtTabChange(
        tabTitle=tab_title, url=url, startTime=start_time)
    tz_for_user = timezone_service.get_tz_for_user(
        "whatever for now")
    updated_tab_change_event = timezone_service.convert_tab_change_timezone(
        some_tab_change_event, tz_for_user)

    start_time = updated_tab_change_event.start_time_with_tz

    assert str(start_time.tzinfo) == local_time_zone

    offset = start_time.utcoffset()
    assert hasattr(offset, "total_seconds") and offset is not None
    offset_hours = int(offset.total_seconds() / 3600)

    assert offset_hours in [regular_tz_offset, daylight_savings_tz_offset]


def test_real_scenario():

    # ### Cook start scenario:
    march_16_at_1_am = datetime(2025, 3, 16, 1, 27, 17)
    event = UtcDtTabChange(tabTitle="foo", url="bar",
                                    startTime=march_16_at_1_am)
    tz_for_user = timezone_service.get_tz_for_user(
        9000)
    updated_tab_change_event = timezone_service.convert_tab_change_timezone(
        event, tz_for_user)

    assert str(
        updated_tab_change_event.start_time_with_tz.tzinfo) == local_time_zone

    offset = updated_tab_change_event.start_time_with_tz.utcoffset()
    assert hasattr(offset, "total_seconds") and offset is not None
    offset_hours = int(offset.total_seconds() / 3600)

    assert offset_hours in [regular_tz_offset, daylight_savings_tz_offset]

    # Test that the new time really really did come out as intended

    output_hours = updated_tab_change_event.start_time_with_tz.hour

    expected_hours = (march_16_at_1_am.hour + regular_tz_offset) % 24
    expected_hours_v2 = (march_16_at_1_am.hour +
                         daylight_savings_tz_offset) % 24

    assert output_hours in [expected_hours, expected_hours_v2]
