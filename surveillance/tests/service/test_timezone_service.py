import pytest

from datetime import datetime

from src.services.services import TimezoneService

from src.config.definitions import local_time_zone, regular_tz_offset, daylight_savings_tz_offset
from src.object.pydantic_dto import TabChangeEvent

timezone_service = TimezoneService()


def test_get_user_timezone():
    tz_for_user = timezone_service.get_tz_for_user(
        "whatever for now")
    assert tz_for_user == local_time_zone


def test_convert_tab_change_timezone():
    tab_title = "World's Best Foo"
    url = "foo.com"
    start_time = datetime.now()
    some_tab_change_event = TabChangeEvent(
        tabTitle=tab_title, url=url, startTime=start_time)
    tz_for_user = timezone_service.get_tz_for_user(
        "whatever for now")
    updated_tab_change_event = timezone_service.convert_tab_change_timezone(
        some_tab_change_event, tz_for_user)

    start_time = updated_tab_change_event.startTime

    assert isinstance(start_time, datetime)

    assert str(start_time.tzinfo) == local_time_zone

    offset = start_time.utcoffset()
    assert hasattr(offset, "total_seconds") and offset is not None
    offset_hours = int(offset.total_seconds() / 3600)

    assert offset_hours in [regular_tz_offset, daylight_savings_tz_offset]
