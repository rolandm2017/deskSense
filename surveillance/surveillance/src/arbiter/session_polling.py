import threading
import time

from surveillance.src.config.definitions import keep_alive_cycle_length, window_push_length
from surveillance.src.object.classes import ProgramSession, ChromeSession

from surveillance.src.util.errors import MissingEngineError


"""
A class responsible for updating the end_time value of the latest Program or Chrome session.

The Arbiter will start recording the current session as soon as it becomes state.

The Arbiter will then conclude the session when the state is replaced by a new current session.

The concluding will occur by the Arbiter 
(a) not sending more pulses and 
(b) passing the finished session to the Summary DAOs to make the end_time precise.
"""

"""
This now does the ten sec window push at the end of a window.

If the session is ended before the ten sec, instead, the used time is added.

Here, worst case scenario in a shutdown situation, is that 0-10 sec is not recorded.
"""

class KeepAliveEngine:
    def __init__(self, session: ProgramSession | ChromeSession, dao_connection):
        """
        This class is a loop. Each iteration of ten loops nudges 
        the end time of the current session forward ten sec.

        The benefit is that the program can shutdown ~whenever~ and
        the end time of the final program will be pretty much accurate,
        while every other program will be bang on.

        The meaning of the interval between iterate_loop() calls is 
        agnostic, dependent on the delay between calls in the container.
        """
        self.session = session
        if session is None:
            raise ValueError("Session should not be None in KeepAliveEngine")
        self.recorder = dao_connection
        self.max_interval = keep_alive_cycle_length  # seconds
        self.amount_used = 0
        self.zero_remainder = 0

    def iterate_loop(self):
        # TODO: Change so that it relies on datetime.now() having 10 sec elapsed.
        self.amount_used += 1  # not
        if self._hit_max_window():
            self._pulse_add_ten()
            self.amount_used = 0

    def conclude(self):
        """
        The "used amount" resets after it reaches a full window. 
        So deducting the full 10 sec should never happen.
        """
        # Skip deduction is it's going to be deducting 10 a fully used window
        amount_of_window_used = self.amount_used

        # self._deduct_remainder(amount_of_window_used)
        self._add_partial_window(amount_of_window_used)

    def _hit_max_window(self):
        return self.max_interval <= self.amount_used

    def _pulse_add_ten(self):
        """
        Go into the session's Summary DAO entry and add ten sec.
        """
        self.recorder.add_ten_sec_to_end_time(self.session)
    
    def _add_partial_window(self, amount_used):
        """
        Used to add amounts between 0 and 9. Incomplete windows.
        """
        self.recorder.add_used_time(amount_used, self.session)

     # For testing: methods to expose internal state
    def get_amount_used(self):
        """Get the current amount used (for testing)"""
        return self.amount_used
    
    def get_session(self):
        """Get the current session (for testing)"""
        return self.session


class ThreadedEngineContainer:
    """
    Runs the KeepAlive signal in a separate thread until the stop signal.

    Does this to keep the ActivityArbiter and the currently active session's window push

    """
    # TODO: Also keep the EngineContainer between engines. just change it out. Keep the thread alive.

    def __init__(self, interval: int | float = 1, sleep_fn=time.sleep, timestamp=None):
        # TODO: Use a sleep interval of like 0.25. Finer granularity.
        self.engine = None
        self.sleep_fn = sleep_fn  # More testable
        self.stop_event = threading.Event()
        self.interval = interval  # seconds - delay between loops
        self.hook_thread = None
        self.is_running = False
        self.timestamp = timestamp

    def add_first_engine(self, engine):
        self.engine = engine

    def start(self):
        """
        Starts updates on the current session
        """
        if not self.is_running:
            self.hook_thread = threading.Thread(target=self._iterate_loop)
            self.hook_thread.daemon = True
            self.hook_thread.start()
            self.is_running = True

    def _iterate_loop(self):
        if self.engine is None:
            raise MissingEngineError()
        while not self.stop_event.is_set():
            self.engine.iterate_loop()  # a second has been used
            self.sleep_fn(self.interval)  # Sleep for 1 second
    
    def replace_engine(self, new_engine):
        """Used to maintain container objects between sessions"""
        if self.engine is None:
            # Expect that add_first_engine is used to initialize.
            raise MissingEngineError()
        
        # NOTE: If you have some sort of off by 1 error, it could be because
        # the current .sleep() hasn't flushed yet, i.e. the prev iteration is still going
        if self.is_running:
            # Stop the current engine's work gracefully
            self.engine.conclude()
            # Swap the engine
            self.engine = new_engine
        else:
            # If the thread isn't running, just set the new engine
            self.engine = new_engine

    def stop(self):
        """
        Stop the current session from receiving anymore updates
        """
        if self.engine is None:
            raise MissingEngineError()
        if self.is_running:
            self.engine.conclude()
            self.stop_event.set()
            if self.hook_thread is not None and self.hook_thread.is_alive():
                self.hook_thread.join(timeout=1)
            self.is_running = False
