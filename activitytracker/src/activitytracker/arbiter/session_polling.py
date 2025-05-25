import threading

import time

from queue import Queue

from activitytracker.config.definitions import (
    keep_alive_cycle_length,
    window_push_length,
)
from activitytracker.object.classes import ChromeSession, ProgramSession
from activitytracker.util.errors import FullWindowError, MissingEngineError

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
        # Reason is that the time.sleep(self.interval) will be ~1.03 sec on average
        self.amount_used += 1  # not
        # print(f"\nin loop {self.amount_used} of 10 for {self.session.get_name()}, ")
        # if self.session.video_info:
        #     print(
        #         "[polling for video] Iterating loop for", self.session.video_info.get_name()
        #     )
        # if self._hit_max_window(self.max_interval, self.amount_used):
        if self._hit_max_window():
            self._pulse_add_ten()
            self.amount_used = 0

    def conclude_engine(self):
        """
        The "used amount" resets after it reaches a full window.
        So deducting the full 10 sec should never happen.

        Said another way, the addition of the full 10 sec
        happens in _pulse_add_ten.
        """
        current_thread = threading.current_thread()
        thread_id = threading.get_ident()
        thread_name = current_thread.name

        print(
            f"[DEBUG] Concluding engine {self.session.get_name()} in thread '{thread_name}' (ID: {thread_id})"
        )

        print(
            f"[DEBUG] Concluding engine {self.session.get_name()} in thread '{thread_name}' (ID: {thread_id})"
        )

        if self.amount_used == window_push_length:
            raise FullWindowError("Used the wrong method to add ten sec")
        self._add_partial_window(self.amount_used)

    def _hit_max_window(self):
        # return max < used
        return self.max_interval <= self.amount_used

    def _pulse_add_ten(self):
        """
        Go into the session's Summary DAO entry and add ten sec.
        """
        self.recorder.add_ten_sec_to_end_time(self.session)

    def _add_partial_window(self, amount_used):
        """
        Used to add amounts between 0 and 9 inclusive. Incomplete windows.

        Note that the Recorder will just do nothing if 0 is sent. This keeps testing simple.
        """
        current_thread = threading.current_thread()
        thread_id = threading.get_ident()
        thread_name = current_thread.name

        if self.session.video_info:
            name = self.session.video_info.get_name()
        else:
            name = self.session.get_name()

        print(
            f"[add_partial_window - engine call] {name} with amount: {amount_used} in thread '{thread_name}' (ID: {thread_id})"
        )
        thread_id_and_name = thread_name + " : " + str(thread_id)
        self.recorder.add_partial_window(amount_used, self.session, thread_id_and_name)


class ThreadedEngineContainer:
    """
    Runs the KeepAlive signal in a separate thread until the stop signal.

    Does this to keep the ActivityArbiter thread free for cvhanges while the
    Engine pulse adds time to sessions, often sleeping for 58 sec of 60.
    """

    def __init__(self, interval: int | float = 1, sleep_fn=time.sleep, profiler=None):
        # TODO: Use a sleep interval of like 0.25. Finer granularity.
        self.interval = interval  # seconds - delay between loops
        self.sleep_fn = sleep_fn  # More testable to inject a func
        self.engine = None
        self.engine_queue = Queue()
        self.stop_event = threading.Event()
        self.hook_thread = None
        self.is_running = False
        self.profiler = profiler

    def add_first_engine(self, engine):
        self.engine = engine

    def start(self):
        """
        Starts updates on the current session
        """
        if not self.is_running:
            self.stop_event.clear()  # Clear the stop event instead of creating a new one

            # Set a custom thread name based on the session
            thread_name = (
                f"KeepAlive-{self.engine.session.get_name()}"
                if self.engine
                else "KeepAlive-Unknown"
            )

            self.hook_thread = threading.Thread(target=self._iterate_loop, name=thread_name)
            self.hook_thread.daemon = True
            self.hook_thread.start()
            self.is_running = True

    # FIXME: This class FOR SURE has problems. I see duplicated prints all the time

    def _iterate_loop(self):
        if self.engine is None:
            raise MissingEngineError()
        # print("while not stop event is set?", self.stop_event.is_set())
        while not self.stop_event.is_set():
            # print(f"Thread {thread_id}")
            while not self.engine_queue.empty():
                old_engine = self.engine
                if old_engine:
                    old_engine.conclude_engine()  # Called from KeepAlive thread!
                self.engine = self.engine_queue.get()

            if self.engine:
                self.engine.iterate_loop()  # a second has been used
                # The sleeping only happens while there is an engine.
                # If there is no engine, there is no sleeping, it just checks if there is a new engine over and over
                self.sleep_fn(self.interval)  # Sleep for 1 second

    def replace_engine(self, new_engine):
        """Used to maintain container objects between sessions"""
        if self.engine is None:
            # Expect that add_first_engine is used to initialize.
            raise MissingEngineError()

        # print(
        #     f"[container - replace_engine] Replacing engine for '{self.engine.session.get_name()}' with '{new_engine.session.get_name()}' in thread '{current_thread.name}' (ID: {thread_id})"
        # )

        # Swap the engine
        # Just queue the new engine, don't stop the thread
        print("Queuing new engine")
        self.engine_queue.put(new_engine)

    def stop(self):
        """
        Stop the current session from receiving anymore updates
        """
        if self.engine is None:
            raise MissingEngineError()
        if self.is_running:
            # Since we're stopping the thread, it
            # doesn't matter which thread calls engine.conclude()
            if self.engine:
                self.engine.conclude_engine()
            self.stop_event.set()
            if self.hook_thread is not None and self.hook_thread.is_alive():
                self.hook_thread.join(timeout=1)
            self.is_running = False
