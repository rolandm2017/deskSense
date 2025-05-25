import time

from activitytracker.arbiter.session_polling import (
    KeepAliveEngine,
    ThreadedEngineContainer,
)
from activitytracker.util.errors import MissingEngineError


# I want this mock to be able to like,
# like, I set it to run 3 full cycles and 3 extra loops
# I want the loops to happen in an instant, because the main pipeline
# won't care whether a threaded sleep happened over 40 sec or 40 CPU cycles.
# The main pipeline is detached completely
# So the test env should be able to be like, cooked, based on some inputs like
# "how long will this session be in the arbiter for?", and then it just
# it just does it. Like you get the calculation by hand, before feeding vals in in the test
# and you feed the Mock, "hey, it's actually going to be, 23 sec" or "it's gonna be 8 sec" or
# "it's gonna be 43 sec"
class MockEngineContainer(ThreadedEngineContainer):
    """
    Is not threaded.

    This mock "just knows" how long the pulse will run for, because the duration is specified.

    Hence the interval arg is just for consistency.
    """

    def __init__(
        self,
        session_durations: list[int],
        interval: int | float = 1,
        sleep_fn=time.sleep,
        timestamp=None,
    ):
        """
        If you submit an inaccurate session_durations here, your test won't work. Be sure it's right!

        duration n = t2 - t1
        duration n + 1 = t3 - t2
        """
        # Time.sleep isn't used
        super().__init__(interval, sleep_fn, timestamp)
        self.session_durations = session_durations or []
        self.duration_index = 0
        self.is_started = False

    def add_first_engine(self, engine):
        return super().add_first_engine(engine)

    def start(self):
        """Start processing - run the first engine with its duration"""
        if self.engine is None:
            raise MissingEngineError()

        if not self.is_started:
            self.is_started = True
            self._run_current_engine()

    def replace_engine(self, new_engine):
        """Replace current engine and run it with the next duration"""
        if self.engine is None:
            raise MissingEngineError()

        # Conclude the old engine
        if self.engine:
            self.engine.conclude_engine()

        # Set the new engine
        self.engine = new_engine
        self.duration_index += 1

        # Run the new engine if we're started
        if self.is_started:
            self._run_current_engine()

    def _run_current_engine(self):
        """Run the current engine for its specified duration"""
        if self.duration_index < len(self.session_durations):
            duration_for_run = self.session_durations[self.duration_index]
            print(f"Running engine for duration: {duration_for_run}")

            for i in range(duration_for_run):
                if self.engine:
                    self.engine.iterate_loop()
        else:
            print("No more durations available")

    def _iterate_loop(self):
        # Not used in mock
        pass

    def stop(self):
        """Stop and conclude the final engine"""
        if self.engine is None:
            raise MissingEngineError()
        if self.engine:
            self.engine.conclude_engine()
        self.is_started = False
