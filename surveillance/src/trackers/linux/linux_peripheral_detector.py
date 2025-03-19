# linux_peripheral_detector.py

from evdev import InputDevice, ecodes

import threading
from datetime import datetime

import os
from dotenv import load_dotenv

from .message_dispatch import publish_keyboard_event, publish_mouse_events

from ...object.classes import MouseAggregate


load_dotenv()

"""
This part of the program runs separately because
1. The rest will live in a Docker container, but
2. This part must stay outside of the container to witness keyboard events, mouse events.

A small benefit, secondary, is
3. It's easier to monitor CPU usage.

There was a fourth reason that is now forgotten. It might be
4. It's easier to run this code all async, limiting async/await contagion, if it's a separate program.
"""

# TODO: The current post request logic might cause overhead, sending many requests for each event. Grouping events together could reduce the load.


# TODO: Consider asynchronous I/O for better performance, allowing more events to be processed without blocking.
#

# TODO: Using a queue to offload POST requests to a worker thread could help instead of creating a new connection per request


class MouseEventAggregator:
    """Really just a named array; the timer will take place outside of it, or else timers are duplicated"""

    def __init__(self):
        self.current_aggregation = []
        self.count = 0

    def add_event(self) -> None | MouseAggregate:
        """A timestamp must be a datetime.timestamp() result."""
        next = self.count + 1
        self.count += 1
        self.current_aggregation.append(next)

    def package_aggregate(self):
        return self.current_aggregation
        # """
        # Aggregate comes out of this class as start_time, end_time, event_count.
        # """
        # start = aggregate.start_time
        # end = aggregate.end_time
        # return MouseAggregate(start, end, aggregate.event_count)

    def reset(self):
        self.current_aggregation = []
        self.count = 0


debug_timeout_ms = 400


class MouseEventDispatch:
    """
    Moving the mouse in any non-tiny manner yields a stream of perhaps 50 to 100 events
    in just a second. So to avoid sending 400 POST requests inside of a few seconds, 
    the dispatch contains a debounce timer and an event aggregator.

    As long as a new event comes in from within the span of the timer, the window
    is kept open for more events to be recorded.

    The goal of this class is to reduce 100-200 POST events per sec
    down to 1-4 POST events per 2-3 sec. Requests have high overhead.
    """

    def __init__(self, event_aggregator, event_ready_handler):
        # fifty_ms = 0.1  # NOTE: 100 ms is a LONG time in mouse move events
        fifty_ms = 0.4  # NOTE: 100 ms is a LONG time in mouse move events
        self.max_delay = debug_timeout_ms / 1000  # ms / 1000 ms/sec
        self.MAX_AGGREGATIONS = 100
        self.event_aggregator = event_aggregator
        self.debounce_timer = None
        self.event_ready_handler = event_ready_handler
        self._timer_lock = threading.Lock()  # Add a lock for thread safety

    def add_to_aggregator(self):
        # Add the event
        if len(self.event_aggregator.current_aggregation) == 0:
            self.start_time = datetime.now()
        self.event_aggregator.add_event()

        # If we've reached the maximum number of events, handle it immediately
        if len(self.event_aggregator.current_aggregation) >= self.MAX_AGGREGATIONS:
            print("beyond max count of aggregates")
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
            print("Starting timer: ", datetime.now().strftime("%M:%S.%f")[:-3])
            self.debounce_timer = threading.Timer(
                self.max_delay, self.handle_finished)
            self.debounce_timer.daemon = True
            self.debounce_timer.start()

    def handle_finished(self):
        # Clear the timer reference
        with self._timer_lock:
            self.debounce_timer = None

        # Process the events
        if len(self.event_aggregator.current_aggregation) > 0:
            print("Event ready handler")
            print("[start]", self.start_time)
            end_time = datetime.now()
            print("[end]", end_time)
            print("[duration]", end_time - self.start_time)
            deliverable = {"type": "mouse",
                           "start": self.start_time, "end": end_time}
            self.event_aggregator.reset()
            self.event_ready_handler(deliverable)


def monitor_keyboard(device_path, send_keyboard_event):
    """
    Monitor keyboard events in a separate thread using the efficient read_loop()

    Keyboard events appear slowly relative to the mouse.
    """
    try:
        keyboard = InputDevice(device_path)
        print(f"Monitoring keyboard: {keyboard.name}")

        for event in keyboard.read_loop():
            is_key_down_event = event.value == 1
            if event.type == ecodes.EV_KEY and is_key_down_event:  # type: ignore
                print(f"Key {event.code} pressed")

                send_keyboard_event()

    except Exception as e:
        print(f"Keyboard monitoring error: {e}")


mouse_aggregator = MouseEventAggregator()


def debug_logger(agg: MouseAggregate):
    print(agg)


def debug_logger_simple():
    print("keyboard event")


mouse_event_handler = publish_mouse_events


mouse_event_dispatch = MouseEventDispatch(
    mouse_aggregator, publish_mouse_events)


def monitor_mouse(device_path):
    """
    Monitor mouse events in a separate thread using the efficient read_loop()

    Note that events show up FAST, like as a rapid stream, think 50-100 a sec of mouse move.

    Captures all relevant mouse events including:
    - Mouse movement (EV_REL with REL_X or REL_Y)
    - Mouse button clicks (EV_KEY)
    - Mouse wheel scrolling (EV_REL with REL_WHEEL or REL_HWHEEL)
    """

    try:
        mouse = InputDevice(device_path)
        print(f"Monitoring mouse: {mouse.name}")

        for event in mouse.read_loop():
            if event.type == ecodes.EV_REL:  # type: ignore
                if event.code == ecodes.REL_X or event.code == ecodes.REL_Y:  # type: ignore
                    # print(f"Mouse moved: {event.value}")
                    # print(

                    # f"Mouse {'X' if event.code == ecodes.REL_X else 'Y'} moved: {event.value}")
                    mouse_event_dispatch.add_to_aggregator()
            elif event.type == ecodes.EV_KEY:  # type: ignore
                button_names = {
                    ecodes.BTN_LEFT: "left",  # type: ignore
                    ecodes.BTN_RIGHT: "right",  # type: ignore
                    ecodes.BTN_MIDDLE: "middle",  # type: ignore
                    ecodes.BTN_SIDE: "side",  # type: ignore
                    ecodes.BTN_EXTRA: "extra"  # type: ignore
                }

                if event.code in button_names:
                    # action = "pressed" if event.value == 1 else "released" if event.value == 0 else "repeated"
                    # button = button_names.get(
                    #     event.code, f"button {event.code}")
                    # print(f"Mouse {button} button {action}")
                    mouse_event_dispatch.add_to_aggregator()

                    # post_mouse_events()
    except Exception as e:
        print(f"Mouse monitoring error: {e}")


if __name__ == "__main__":
    # Device paths
    keyboard_path = os.getenv("UBUNTU_KEYBOARD_PATH")
    mouse_path = os.getenv("UBUNTU_MOUSE_PATH")

    MODE = "DEBUG"  # Clue for developer, not actually used

    timeout_ms = 50
    mouse_aggregator = MouseEventAggregator()

    # Create event dispatch with conditional handler based on debug mode
    mouse_event_dispatch = MouseEventDispatch(
        mouse_aggregator, debug_logger
    )

    # Create and start threads
    keyboard_thread = threading.Thread(
        target=monitor_keyboard,
        args=(keyboard_path, debug_logger_simple),
        daemon=True
    )

    mouse_thread = threading.Thread(
        target=monitor_mouse,
        args=(mouse_path, mouse_event_dispatch),
        daemon=True
    )

    keyboard_thread.start()
    mouse_thread.start()

    try:
        # Keep the main thread alive
        keyboard_thread.join()
        mouse_thread.join()
    except KeyboardInterrupt:
        print("Monitoring stopped")
