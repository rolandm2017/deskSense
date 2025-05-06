import threading
from datetime import datetime


class MouseEventDispatch:
    """
    Moving the mouse in any non-tiny manner yields a stream of perhaps 50 to 100 events
    in just a second. So to avoid sending 400 POST requests inside of a few seconds, 
    the dispatch contains a debounce timer and an event aggregator.

    As long as a new event comes in from within the span of the timer, the window
    is kept open for more events to be recorded.

    The goal of this class is to reduce 100-200 events per sec
    down to 1-4 events per 2-3 sec. Requests have high overhead.
    """

    def __init__(self, event_aggregator, event_ready_handler):
        # fifty_ms = 0.1  # NOTE: 100 ms is a LONG time in mouse move events
        debug_timeout_ms = 300  # NOTE: 300 ms is a LONG time in mouse move events
        ms_per_sec = 1000
        self.max_delay_for_end_bundle = debug_timeout_ms / ms_per_sec  # ms / 1000 ms/sec
        # NOTE about max_agg: 300 is for programming, but 1200 is for FPS
        self.MAX_AGGREGATIONS = 1000  # in a single package
        self.event_aggregator = event_aggregator
        self.debounce_timer = None
        self.event_ready_handler = event_ready_handler
        self._timer_lock = threading.Lock()  # Add a lock for thread safety
        self.fun_counter = 0

    def add_to_aggregator(self):
        # Add the event
        if len(self.event_aggregator.current_aggregation) == 0:
            self.start_time = datetime.now()
        self.event_aggregator.add_event()

        # If we've reached the maximum number of events, handle it immediately
        if len(self.event_aggregator.current_aggregation) >= self.MAX_AGGREGATIONS:
            print("--> beyond max count of aggregates: " + str(self.fun_counter))
            self.fun_counter += 1
            with self._timer_lock:
                if self.debounce_timer:
                    self.debounce_timer.cancel()
                    self.debounce_timer = None
            self.handle_finished()
            return

        # Cancel any existing timer
        with self._timer_lock:
            if self.debounce_timer:
                self.debounce_timer.cancel()
                self.debounce_timer = None

            # Create a new timer
            self.debounce_timer = threading.Timer(
                self.max_delay_for_end_bundle, self.handle_finished)
            self.debounce_timer.daemon = True
            self.debounce_timer.start()

    def handle_finished(self):
        # Clear the timer reference
        with self._timer_lock:
            self.debounce_timer = None

        # Process the events
        if len(self.event_aggregator.current_aggregation) > 0:
            # print("Event ready handler")
            # print("[start]", self.start_time)
            end_time = datetime.now()
            # print("[end]", end_time)
            # print("[duration]", end_time - self.start_time)
            end_time = end_time.timestamp()
            deliverable = {"type": "mouse",
                           "start": self.start_time.timestamp(), "end": end_time}
            self.event_aggregator.reset()
            self.event_ready_handler(deliverable)
