import threading
import asyncio
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


class KeepAliveEngine:
    def __init__(self, session, dao_connection, loop):
        """
        This class is a loop. Each iteration of ten loops nudges 
        the end time of the current session forward ten sec.

        The benefit is that the program can shutdown ~whenever~ and
        the end time of the final program will be pretty much accurate,
        while every other program will be bang on.
        """
        self.session = session
        self.dao = dao_connection
        self.max_interval = 10  # seconds
        self.elapsed = 0
        self.loop = loop

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
        print("Pulse add ten, 54ru")
        async_task = self.dao.add_ten_sec_to_end_time(self.session)
        # FIXME: this isn't reached
        if asyncio.iscoroutine(async_task):
            self.loop.create_task(async_task)

    def _deduct_remainder(self, remainder):
        """
        The loop was t seconds into the 10 second window, and was ended early.

        Thus we deduct 10 - t seconds from the session's end time.

        "Here's how much time was left unfinished in that window. Please remove it."
        """
        duration = self.calculate_remaining_window(remainder)
        async_task = self.dao.deduct_duration(duration, self.session)
        if asyncio.iscoroutine(async_task):
            self.loop.create_task(async_task)

    def calculate_remaining_window(self, used_amount):
        window_length = self.max_interval  # 10
        remaining = window_length - used_amount
        return remaining
    
    def save_loop_for_reuse(self):
        """Less resources if you reuse a loop instead of making a new one"""
        return self.loop

class ThreadedEngineContainer:
    """
    Runs the KeepAlive signal in a separate thread until the stop signal.

    Does this to keep the ActivityArbiter and the currently active session's window push

    # TODO: Also keep the EngineContainer between engines. just change it out. Keep the thread alive.
    """
    def __init__(self, engine: KeepAliveEngine, interval=1, sleep_fn=time.sleep):
        self.engine = engine
        self.sleep_fn = sleep_fn  # More testable
        self.stop_event = threading.Event()
        self.interval = interval  # seconds - delay between loops
        self.hook_thread = None
        self.is_running = False

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
        while not self.stop_event.is_set():
            self.engine.iterate_loop()
            self.sleep_fn(self.interval)  # Sleep for 1 second

    def stop(self):
        """
        Stop the current session from receiving anymore updates
        """
        if self.is_running:
            self.engine.conclude()
            self.stop_event.set()
            if self.hook_thread is not None and self.hook_thread.is_alive():
                self.hook_thread.join(timeout=1)
            self.is_running = False
        