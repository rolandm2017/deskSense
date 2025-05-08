import pytest

from datetime import datetime

from activitytracker.object.classes import ProgramSession, ProgramSessionDict
from activitytracker.util.time_wrappers import UserLocalTime

from ...helper.deepcopy_test_data import deepcopy_test_data


def fmt_time_string(s):
    return datetime.fromisoformat(s)


imaginary_path_to_chrome = "C:/Programs/imaginary/path/to/Chrome.exe"
imaginary_chrome_processe = "Chrome.exe"


@pytest.fixture
def program_path_test_events():
    session1 = ProgramSession(
        exe_path=imaginary_path_to_chrome,
        process_name=imaginary_chrome_processe,
        window_title="Google Chrome",
        detail="X. It's what's happening / X",
        start_time=UserLocalTime(fmt_time_string("2025-03-22 16:14:50.201399-07:00")),
        productive=False,
    )
    session2 = ProgramSession(
        exe_path="C:/wherever/you/find/Postman.exe",
        process_name="Xorg",
        window_title="My Workspace",
        detail="dash | Overview",
        start_time=UserLocalTime(
            fmt_time_string("2025-03-22 16:15:55.237392-07:00")
        ),  # Roughly 65 sec difference
        productive=False,
    )
    session3 = ProgramSession(
        exe_path="C:/path/to/VSCode.exe",
        process_name="Code.exe",
        window_title="Visual Studio Code",
        detail="surveillance_manager.py - deskSense",
        start_time=UserLocalTime(
            fmt_time_string("2025-03-22 16:16:03.374304-07:00")
        ),  # Roughly 8 sec difference
        productive=False,
    )
    session4 = ProgramSession(
        # NOTE: Manual change from Gnome Shell to a second Chrome entry
        exe_path=imaginary_path_to_chrome,
        process_name=imaginary_chrome_processe,
        window_title="Google Chrome",
        detail="TikTok: Waste Your Time Today!",
        start_time=UserLocalTime(
            fmt_time_string("2025-03-22 16:16:17.480951-07:00")
        ),  # Roughly 14 sec difference
        productive=False,
    )
    test_events = [session1, session2, session3, session4]

    return test_events


@pytest.fixture(scope="function")
def validate_test_data_and_get_durations(program_path_test_events):
    """Exists to ensure no PEBKAC. 'The data really does say what was intended.'"""

    # Validate your dummy test data
    durations_for_sessions = []
    for i in range(0, 4):
        assert isinstance(program_path_test_events[i].start_time, UserLocalTime)
        assert isinstance(program_path_test_events[i].start_time.dt, datetime)
        assert program_path_test_events[i].start_time.dt.tzinfo is not None

        if i == 3:
            break  # There is no 4th value
        assert (
            program_path_test_events[i].start_time < program_path_test_events[i + 1].start_time
        ), "Events must be chronological"

        elapsed_between_sessions = int(
            (
                program_path_test_events[i + 1].start_time
                - program_path_test_events[i].start_time
            ).total_seconds()
        )
        durations_for_sessions.append(elapsed_between_sessions)

    clones = deepcopy_test_data(program_path_test_events)
    print("enumerating clones")
    for i, c in enumerate(clones):
        print(i, c.start_time)
    return clones, durations_for_sessions
