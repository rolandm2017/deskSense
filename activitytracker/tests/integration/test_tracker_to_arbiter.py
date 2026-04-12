from datetime import datetime

from activitytracker.config.definitions import no_space_dash_space
from activitytracker.object.classes import ProgramSession
from activitytracker.trackers.program_tracker import ProgramTrackerCore
from activitytracker.util.program_tools import contains_space_dash_space, separate_window_name_and_detail
from activitytracker.util.time_wrappers import UserLocalTime

from ..data.captures_for_test_data_programs import program_data
from ..mocks.mock_clock import UserLocalTimeMockClock


class MockProgramFacade:
    def __init__(self, events):
        self.events = events

    def listen_for_window_changes(self):
        for event in self.events:
            yield event


class CapturingArbiter:
    def __init__(self):
        self.received_program_sessions = []

    def set_program_state(self, session):
        self.received_program_sessions.append(session)


def _expected_window_and_detail(raw_window_title):
    if contains_space_dash_space(raw_window_title):
        return separate_window_name_and_detail(raw_window_title)
    return no_space_dash_space, raw_window_title


def test_program_tracker_forwards_program_sessions_to_arbiter():
    facade_events = [entry["event"] for entry in program_data]
    event_times = [UserLocalTime(datetime.fromisoformat(entry["time"])) for entry in program_data]
    tracker_clock = UserLocalTimeMockClock(event_times)
    program_facade = MockProgramFacade(facade_events)
    arbiter = CapturingArbiter()

    tracker = ProgramTrackerCore(
        tracker_clock,
        program_facade,
        window_change_handler=arbiter.set_program_state,
    )

    tracker.run_tracking_loop()

    assert len(arbiter.received_program_sessions) == len(facade_events)

    for index, session in enumerate(arbiter.received_program_sessions):
        source_event = facade_events[index]
        expected_detail, expected_window_title = _expected_window_and_detail(
            source_event["window_title"]
        )
        assert isinstance(session, ProgramSession)
        assert session.exe_path == source_event["exe_path"]
        assert session.process_name == source_event["process_name"]
        assert session.window_title == expected_window_title
        assert session.detail == expected_detail
        assert session.start_time.dt == event_times[index].dt
        assert session.end_time is None
        assert session.duration is None
