from activitytracker.util.copy_util import snapshot_obj_for_tests


class RecordingActivityRecorder:
    """
    Test double for ActivityRecorder.

    Captures arbiter->recorder interactions in simple lists so tests can
    assert routing behavior without spying on DAO calls.
    """

    def __init__(self):
        self.new_sessions = []
        self.concluded_sessions = []
        self.full_windows = []
        self.partial_windows = []

    def on_new_session(self, session):
        self.new_sessions.append(snapshot_obj_for_tests(session))

    def on_state_changed(self, session):
        if session is not None:
            self.concluded_sessions.append(snapshot_obj_for_tests(session))

    def add_ten_sec_to_end_time(self, session):
        self.full_windows.append(snapshot_obj_for_tests(session))

    def add_partial_window(self, amount, session):
        self.partial_windows.append((amount, snapshot_obj_for_tests(session)))
