import time

from surveillance.src.arbiter.session_heartbeat import ThreadedEngineContainer
from surveillance.src.arbiter.session_heartbeat import KeepAliveEngine



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
    """

    def __init__(self, engine: KeepAliveEngine, interval: int | float = 1, sleep_fn=time.sleep, timestamp=None):
        # Time.sleep isn't used
        super().__init__(engine, interval, sleep_fn, timestamp)

    def start(self, duration):
        for i in range(0, duration):
            self.engine.iterate_loop()
        
    def _iterate_loop(self):
        pass

    def stop(self):
        self.engine.conclude()
