from activitytracker.object.classes import ChromeSession
from activitytracker.services.chrome_service import ChromeService
from activitytracker.services.timezone_service import TimezoneService
from activitytracker.util.time_wrappers import UserLocalTime

from ..data.captures_for_test_data_Chrome import chrome_data
from ..mocks.mock_clock import MockClock


class CapturingArbiter:
    def __init__(self):
        self.received_tabs = []

    def set_tab_state(self, session):
        self.received_tabs.append(session)


def test_chrome_service_emits_sessions_to_arbiter():
    timezone_service = TimezoneService()
    user_tz = timezone_service.get_tz_for_user(1)
    converted_events = [
        timezone_service.convert_tab_change_timezone(event, user_tz) for event in chrome_data
    ]

    clock = MockClock([event.startTime for event in chrome_data])
    arbiter = CapturingArbiter()
    chrome_service = ChromeService(clock, arbiter=arbiter)
    chrome_service.event_emitter.on("tab_change", arbiter.set_tab_state)

    for event in converted_events:
        chrome_service.log_tab_event(event)

    assert len(arbiter.received_tabs) == len(chrome_data)

    for index, session in enumerate(arbiter.received_tabs):
        source_event = chrome_data[index]
        converted_event = converted_events[index]
        assert isinstance(session, ChromeSession)
        assert session.domain == source_event.url
        assert session.detail == source_event.tabTitle
        assert isinstance(session.start_time, UserLocalTime)
        assert session.start_time.dt == converted_event.start_time_with_tz.dt
        assert session.end_time is None
        assert session.duration is None
