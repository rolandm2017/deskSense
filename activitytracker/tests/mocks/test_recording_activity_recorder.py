from datetime import datetime, timedelta

from activitytracker.object.classes import ProgramSession
from activitytracker.util.time_wrappers import UserLocalTime

from .recording_activity_recorder import RecordingActivityRecorder


def make_program_session(start_time):
    return ProgramSession(
        "some/exe/path.exe",
        "path.exe",
        "Visual Studio Code",
        "myfile.py",
        UserLocalTime(start_time),
    )


def test_recording_activity_recorder_captures_all_call_types():
    recorder = RecordingActivityRecorder()
    t1 = datetime.now().astimezone()
    t2 = t1 + timedelta(seconds=8)

    new_session = make_program_session(t1)
    concluded_session = new_session.to_completed(UserLocalTime(t2))
    concluded_session.duration = t2 - t1

    recorder.on_new_session(new_session)
    recorder.on_state_changed(concluded_session)
    recorder.add_ten_sec_to_end_time(new_session)
    recorder.add_partial_window(3, new_session)

    assert len(recorder.new_sessions) == 1
    assert len(recorder.concluded_sessions) == 1
    assert len(recorder.full_windows) == 1
    assert len(recorder.partial_windows) == 1

    assert recorder.new_sessions[0].start_time == new_session.start_time
    assert recorder.concluded_sessions[0].duration == t2 - t1
    assert recorder.full_windows[0].start_time == new_session.start_time

    partial_amount, partial_session = recorder.partial_windows[0]
    assert partial_amount == 3
    assert partial_session.start_time == new_session.start_time


def test_recording_activity_recorder_ignores_none_state_changed():
    recorder = RecordingActivityRecorder()
    recorder.on_state_changed(None)
    assert recorder.concluded_sessions == []
