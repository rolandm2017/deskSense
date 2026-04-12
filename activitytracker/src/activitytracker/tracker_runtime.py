from activitytracker.util.threaded_tracker import ThreadedTracker


class TrackerRuntime:
    def __init__(
        self,
        keyboard_tracker,
        mouse_tracker,
        program_tracker,
        threaded_tracker_class=ThreadedTracker,
    ):
        self.keyboard_thread = threaded_tracker_class(keyboard_tracker)
        self.mouse_thread = threaded_tracker_class(mouse_tracker)
        self.program_thread = threaded_tracker_class(program_tracker)

    def start(self):
        self.keyboard_thread.start()
        self.mouse_thread.start()
        self.program_thread.start()

    def stop(self):
        self.keyboard_thread.stop()
        self.mouse_thread.stop()
        self.program_thread.stop()
