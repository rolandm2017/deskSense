# linux_peripheral_detector.py
from evdev import InputDevice, ecodes

import threading
import asyncio
from datetime import datetime

from time import monotonic

import os
from dotenv import load_dotenv

from .linux_api import post_keyboard_event, post_mouse_events

from ...object.classes import PeripheralAggregate

from ...util.mouse_aggregator import MouseEventAggregator
from ...util.clock import SystemClock

load_dotenv()


class MouseMoveEvent:
    def __init__(self, time):
        self.time = time


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
        fifty_ms = 0.05  # NOTE: 100 ms is a LONG time in mouse move events
        self.max_delay = fifty_ms
        self.MAX_AGGREGATIONS = 100
        self.event_aggregator: MouseEventAggregator = event_aggregator
        self.debounce_timer = None
        self.event_ready_handler = event_ready_handler

    def add_to_aggregator(self, mouse_event: float):
        # TODO: So you startt he aggregate with a datetime, then track time differences with a monotonic,
        # TODO Then conclude it with another datetime

        # TODO: On start new aggregate, record the time. I mean a datetime.
        # TODO: On conclude an aggregate, record the end_time as datetime.
        # TODO: Still use monotonic to decide when sufficient time has passed.
        self.event_aggregator.add_event(mouse_event)

        if self.event_aggregator.current_aggregation and self.event_aggregator.current_aggregation.event_count >= self.MAX_AGGREGATIONS:
            assert self.debounce_timer is not None, "Debounce timer was None when it should exist"
            self.debounce_timer.cancel()
            self.handle_finished()
            return

        if self.debounce_timer:
            self.debounce_timer.cancel()

        self.debounce_timer = threading.Timer(
            self.max_delay, self.handle_finished)
        self.debounce_timer.daemon = True
        self.debounce_timer.start()

    def handle_finished(self):
        possibly_aggregate = self.event_aggregator.current_aggregation

        if possibly_aggregate is not None:
            aggregate_to_complete = possibly_aggregate
            finished_aggregate = self.event_aggregator.package_aggregate(
                aggregate_to_complete)
            self.event_ready_handler(finished_aggregate)

    # async def debounced_process(self):
    #     await asyncio.sleep(self.max_delay)
    #     await self.event_ready_handler()


def monitor_keyboard(device_path, post_keyboard_event):
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

                post_keyboard_event()

    except Exception as e:
        print(f"Keyboard monitoring error: {e}")


clock = SystemClock()

timeout_ms = 50
mouse_aggregator = MouseEventAggregator(clock, timeout_ms)


def debug_logger(agg: PeripheralAggregate):
    print(agg)


def debug_logger_simple():
    print("keyboard event")


mouse_event_handler = post_mouse_events


mouse_event_dispatch = MouseEventDispatch(mouse_aggregator, post_mouse_events)


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
                    now = monotonic()
                    mouse_event_dispatch.add_to_aggregator(now)
            elif event.type == ecodes.EV_KEY:  # type: ignore
                button_names = {
                    ecodes.BTN_LEFT: "left",  # type: ignore
                    ecodes.BTN_RIGHT: "right",  # type: ignore
                    ecodes.BTN_MIDDLE: "middle",  # type: ignore
                    ecodes.BTN_SIDE: "side",  # type: ignore
                    ecodes.BTN_EXTRA: "extra"  # type: ignore
                }

                if event.code in button_names:
                    action = "pressed" if event.value == 1 else "released" if event.value == 0 else "repeated"
                    button = button_names.get(
                        event.code, f"button {event.code}")
                    print(f"Mouse {button} button {action}")
                    mouse_event_dispatch.add_to_aggregator(now)

                    # post_mouse_events()
    except Exception as e:
        print(f"Mouse monitoring error: {e}")


if __name__ == "__main__":
    # Device paths
    keyboard_path = os.getenv("UBUNTU_KEYBOARD_PATH")
    mouse_path = os.getenv("UBUNTU_MOUSE_PATH")

    MODE = "DEBUG"

    # Initialize the clock and aggregator
    clock = SystemClock()
    timeout_ms = 50
    mouse_aggregator = MouseEventAggregator(clock, timeout_ms)

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
