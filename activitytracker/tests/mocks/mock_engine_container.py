import time

from activitytracker.arbiter.session_polling import ThreadedEngineContainer
from activitytracker.arbiter.session_polling import KeepAliveEngine

from activitytracker.util.errors import MissingEngineError


# TODO:
# I want this mock to be able to like
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

    def __init__(self, session_durations: list[int], interval: int | float = 1, sleep_fn=time.sleep, timestamp=None):
        """
        If you submit an inaccurate session_durations here, your test won't work. Be sure it's right!

        duration n = t2 - t1
        duration n + 1 = t3 - t2
        """
        # Time.sleep isn't used
        super().__init__(interval, sleep_fn, timestamp)
        self.session_durations = session_durations or []
        self.duration_iter = iter(self.session_durations)
        self.count = 0

    def add_first_engine(self, engine):
        return super().add_first_engine(engine)

    def start(self):
        if self.engine is None:
            raise MissingEngineError()
        # Get the duration for the nth run from the iter
        try:
            duration_for_run = next(self.duration_iter)
            self.count += 1  # Increment the count here
            print(f"duration for run: {duration_for_run} in run {self.count}")
            for i in range(0, duration_for_run):
                self.engine.iterate_loop()
        except StopIteration:
            print("No more durations available in the iterator")

    def _iterate_loop(self):
        pass

    def stop(self):
        if self.engine is None:
            raise MissingEngineError()
        self.engine.conclude()
