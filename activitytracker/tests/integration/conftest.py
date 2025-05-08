import pytest

from datetime import datetime

from activitytracker.util.time_wrappers import UserLocalTime

from ..data.program_session_path import test_events
from ..helper.deepcopy_test_data import deepcopy_test_data


@pytest.fixture(scope="module")
def validate_test_data_and_get_durations():
    """Exists to ensure no PEBKAC. 'The data really does say what was intended.'"""
    # Validate your dummy test data
    durations_for_sessions = []
    for i in range(0, 4):
        assert isinstance(test_events[i].start_time, UserLocalTime)
        assert isinstance(test_events[i].start_time.dt, datetime)
        assert test_events[i].start_time.dt.tzinfo is not None

        if i == 3:
            break  # There is no 4th value
        assert (
            test_events[i].start_time < test_events[i + 1].start_time
        ), "Events must be chronological"

        elapsed_between_sessions = int(
            (test_events[i + 1].start_time - test_events[i].start_time).total_seconds()
        )
        durations_for_sessions.append(elapsed_between_sessions)

    # Return the data to the test
    clones = deepcopy_test_data(test_events)
    return clones, durations_for_sessions
