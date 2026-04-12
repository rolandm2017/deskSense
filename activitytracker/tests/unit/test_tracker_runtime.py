import pytest

from activitytracker.tracker_runtime import TrackerRuntime


class RecordingThreadedTracker:
    instances = []

    def __init__(self, core_tracker):
        self.core_tracker = core_tracker
        self.started = False
        self.stopped = False
        self.__class__.instances.append(self)

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True


class StopErrorThreadedTracker(RecordingThreadedTracker):
    def stop(self):
        self.stopped = True
        raise RuntimeError("stop failed")


def test_start_starts_keyboard_mouse_and_program_trackers():
    RecordingThreadedTracker.instances = []
    keyboard_tracker = object()
    mouse_tracker = object()
    program_tracker = object()

    runtime = TrackerRuntime(
        keyboard_tracker,
        mouse_tracker,
        program_tracker,
        threaded_tracker_class=RecordingThreadedTracker,
    )

    runtime.start()

    assert [tracker.core_tracker for tracker in RecordingThreadedTracker.instances] == [
        keyboard_tracker,
        mouse_tracker,
        program_tracker,
    ]
    assert all(tracker.started for tracker in RecordingThreadedTracker.instances)


def test_stop_stops_keyboard_mouse_and_program_trackers():
    RecordingThreadedTracker.instances = []
    runtime = TrackerRuntime(
        object(),
        object(),
        object(),
        threaded_tracker_class=RecordingThreadedTracker,
    )

    runtime.stop()

    assert all(tracker.stopped for tracker in RecordingThreadedTracker.instances)


def test_stop_error_propagates_and_skips_later_trackers():
    StopErrorThreadedTracker.instances = []
    runtime = TrackerRuntime(
        object(),
        object(),
        object(),
        threaded_tracker_class=StopErrorThreadedTracker,
    )

    with pytest.raises(RuntimeError, match="stop failed"):
        runtime.stop()

    assert StopErrorThreadedTracker.instances[0].stopped is True
    assert StopErrorThreadedTracker.instances[1].stopped is False
    assert StopErrorThreadedTracker.instances[2].stopped is False
