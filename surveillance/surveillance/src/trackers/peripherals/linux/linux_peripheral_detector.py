# linux_peripheral_detector.py
"""
This part of the program runs separately because
1. The rest will live in a Docker container, but
2. This part must stay outside of the container to witness keyboard events, mouse events.

** Please note that this part of the program MUST live outside of the container. **

A small benefit, secondary, is
3. It's easier to monitor CPU usage.

There was a fourth reason that is now forgotten. It might be
4. It's easier to run this code all async, limiting async/await contagion, if it's a separate program.
"""

from evdev import InputDevice, ecodes

import threading
from datetime import datetime

import os
from dotenv import load_dotenv

from surveillance.src.trackers.message_dispatch import publish_keyboard_event, publish_mouse_events

from surveillance.src.trackers.peripherals.util.mouse_event_aggregator import MouseEventAggregator
from surveillance.src.trackers.peripherals.util.mouse_event_dispatch import MouseEventDispatch

from surveillance.src.object.classes import MouseAggregate

load_dotenv()


# TODO: Consider asynchronous I/O for better performance, allowing more events to be processed without blocking.



def linux_monitor_keyboard(device_path, send_keyboard_event):
    """
    Monitor keyboard events in a separate thread using the efficient read_loop()

    Keyboard events appear slowly relative to the mouse.
    """
    try:
        print("path:", device_path, send_keyboard_event)
        keyboard = InputDevice(device_path)
        print(f"Monitoring keyboard: {keyboard.name}")

        for event in keyboard.read_loop():
            is_key_down_event = event.value == 1
            if event.type == ecodes.EV_KEY and is_key_down_event:  # type: ignore
                # print(f"Key {event.code} pressed")

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


def linux_monitor_mouse(device_path):
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
                    # pass
            elif event.type == ecodes.EV_KEY:  # type: ignore
                button_names = {
                    ecodes.BTN_LEFT: "left",  # type: ignore
                    ecodes.BTN_RIGHT: "right",  # type: ignore
                    ecodes.BTN_MIDDLE: "middle",  # type: ignore
                    ecodes.BTN_SIDE: "side",  # type: ignore
                    ecodes.BTN_EXTRA: "extra"  # type: ignore
                }

                if event.code in button_names:
                    # pass
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
        target=linux_monitor_keyboard,
        args=(keyboard_path, debug_logger_simple),
        daemon=True
    )

    mouse_thread = threading.Thread(
        target=linux_monitor_mouse,
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
