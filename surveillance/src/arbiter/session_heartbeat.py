import threading
import time

from datetime import timedelta

"""
A class responsible for updating the end_time value of the latest Program or Chrome session.

NOTE that the Arbiter will start recording the current session as soon as it becomes state.

The Arbiter will then conclude the session when the state is replaced by a new current session.

The concluding will occur by the Arbiter 
(a) not sending more heartbeats and 
(b) passing the finished session to the Summary DAOs to make the end_time precise.
"""

class SessionHeartbeat:
    def __init__(self, session, dao_connection, sleep_fn=time.sleep):
        self.session = session
        self.dao = dao_connection
        self.interval = 1  # seconds
        self.max_interval = 10  # seconds
        self.stop_event = threading.Event()
        self.hook_thread = None
        self.is_running = False
        self.sleep_fn = sleep_fn  # More testable
        self._loop_count = 0 

    def start(self):
        """
        Starts updates on the current session
        """
        self.hook_thread = threading.Thread(target=self._run_heartbeat)
        self.hook_thread.daemon = True
        self.hook_thread.start()
        self.is_running = True

    def _run_heartbeat(self):
        elapsed = 0
        while not self.stop_event.is_set():
            elapsed += 1
            self._loop_count += 1  # for testing
            self.sleep_fn(self.interval)  # Use injected sleep function
            if self._hit_max_window(elapsed):
                self._pulse_add_ten()
                elapsed = 0
        # Conclude by deducting the part we didn't get to
        self._deduct_remainder(elapsed)

    def _hit_max_window(self, duration):
        return self.max_interval <= duration

    def _pulse_add_ten(self):
        """
        Go into the session's Summary DAO entry and add ten sec.
        """
        # current_end_time = self.dao.get_end_for_session(session)
        # updated_end_time = current_end_time + timedelta(seconds=10)
        self.dao.add_ten_sec_to_end_time(self.session)

    def _deduct_remainder(self, remainder):
        """
        The loop was t seconds into the 10 second window, and was ended early.

        Thus we deduct 10 - t seconds from the session's end time.

        "Here's how much time was left unfinished in that window. Please remove it."
        """
        duration = 10 - remainder
        self.dao.deduct_duration(duration, self.session)
    
    def stop(self):
        """
        Stop the current session from receiving anymore updates
        """
        self.stop_event.set()
        if self.hook_thread is not None and self.hook_thread.is_alive():
            self.hook_thread.join(timeout=1)
        self.is_running = False



class KeepAliveEngine:
    def __init__(self, session, dao_connection):
        """
        This class is a loop.
        """
        self.session = session
        self.dao = dao_connection
        self.interval = 1  # seconds
        self.max_interval = 10  # seconds
        self.elapsed = 0

    def iterate_loop(self):
        self.elapsed += 1
        if self._hit_max_window():
            self._pulse_add_ten()
            self.elapsed = 0

    def conclude(self):
        self._deduct_remainder(self.elapsed)

    def _hit_max_window(self):
        return self.max_interval <= self.elapsed

    def _pulse_add_ten(self):
        """
        Go into the session's Summary DAO entry and add ten sec.
        """
        # current_end_time = self.dao.get_end_for_session(session)
        # updated_end_time = current_end_time + timedelta(seconds=10)
        self.dao.add_ten_sec_to_end_time(self.session)

    def _deduct_remainder(self, remainder):
        """
        The loop was t seconds into the 10 second window, and was ended early.

        Thus we deduct 10 - t seconds from the session's end time.

        "Here's how much time was left unfinished in that window. Please remove it."
        """
        duration = self.calculate_remaining_window(remainder)
        self.dao.deduct_duration(duration, self.session)

    def calculate_remaining_window(self, used_amount):
        window_length = self.max_interval  # 10
        remaining = window_length - used_amount
        return remaining

class ThreadedEngineContainer:
    def __init__(self, engine: KeepAliveEngine, sleep_fn=time.sleep):
        self.engine = engine
        self.sleep_fn = sleep_fn  # More testable

    def start(self):
        """
        Starts updates on the current session
        """
        self.hook_thread = threading.Thread(target=self._iterate_loop)
        self.hook_thread.daemon = True
        self.hook_thread.start()
        self.is_running = True
        
    def _iterate_loop(self):
        while not self.stop_event.is_set():
            self.engine.iterate()
            self.sleep_fn(1)  # Sleep for 1 second

    def stop(self):
        """
        Stop the current session from receiving anymore updates
        """
        self.engine.conclude()
        self.stop_event.set()
        if self.hook_thread is not None and self.hook_thread.is_alive():
            self.hook_thread.join(timeout=1)
        self.is_running = False
        