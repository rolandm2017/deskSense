from evdev import InputDevice, ecodes
import threading

import requests
from requests.exceptions import RequestException
import time

import os
from dotenv import load_dotenv

from ...util.mouse_aggregator import MouseEventAggregator

load_dotenv()

server_endpoint = os.getenv("PATH_TO_PERIPHERALS_ENDPOINT")

if server_endpoint is None:
    raise ValueError("Failed to load DeskSense peripherals endpoint")

keyboard_endpoint = server_endpoint + "/keyboard"
mouse_endpoint = server_endpoint + "/mouse"


def post_keyboard_event():
    """
    Send an empty POST request when a keyboard event is detected.

    Assumes the program will always be informing 
    another program on the same machine, < 1.00 milliseconds away.
    """
    try:
        # timestamp = time.time()
        # payload = {'timestamp': timestamp}  # Can add "json=payload" to .post() to send the time.
        # Basic empty POST request
        response = requests.post(keyboard_endpoint)

        # Optional: Check if the request was successful
        if response.status_code == 200:
            print("POST request successful")
        else:
            # TODO: Log the failure
            print(
                f"POST request failed with status code: {response.status_code}")

    except RequestException as err:
        print(f"POST request error: {err}")


def post_mouse_events():
    """
    Send an empty POST request when a keyboard event is detected.

    Assumes the program will always be informing 
    another program on the same machine, < 1.00 milliseconds away.
    """
    try:
        response = requests.post(mouse_endpoint)

        # Optional: Check if the request was successful
        if response.status_code == 200:
            print("POST request successful")
        else:
            # TODO: Log the failure
            print(
                f"POST request failed with status code: {response.status_code}")

    except RequestException as err:
        print(f"POST request error: {err}")


def monitor_keyboard(device_path):
    """
    Monitor keyboard events in a separate thread using the efficient read_loop()

    Keyboard events appear slowly relative to the mouse.
    """
    try:
        keyboard = InputDevice(device_path)
        print(f"Monitoring keyboard: {keyboard.name}")

        for event in keyboard.read_loop():
            if event.type == ecodes.EV_KEY and event.value == 1:  # Key down events
                print(f"Key {event.code} pressed")

                post_keyboard_event()
    except Exception as e:
        print(f"Keyboard monitoring error: {e}")


def monitor_mouse(device_path):
    """
    Monitor mouse events in a separate thread using the efficient read_loop()

    Note that events show up FAST, like as a rapid stream, think 50-100 a sec of mouse move.
    """
    try:
        mouse = InputDevice(device_path)
        print(f"Monitoring mouse: {mouse.name}")

        for event in mouse.read_loop():
            if event.type == ecodes.EV_REL:
                if event.code == ecodes.REL_X or event.code == ecodes.REL_Y:
                    print(
                        f"Mouse {'X' if event.code == ecodes.REL_X else 'Y'} moved: {event.value}")
                    # Here you could send HTTP POST request instead of printing
    except Exception as e:
        print(f"Mouse monitoring error: {e}")


if __name__ == "__main__":
    # Device paths
    keyboard_path = os.getenv("UBUNTU_KEYBOARD_PATH")
    mouse_path = os.getenv("UBUNTU_MOUSE_PATH")

    if keyboard_path is None or mouse_path is None:
        raise ValueError("Failed to load peripheral paths")

    # Create and start threads
    keyboard_thread = threading.Thread(
        target=monitor_keyboard, args=(keyboard_path,), daemon=True)
    mouse_thread = threading.Thread(
        target=monitor_mouse, args=(mouse_path,), daemon=True)

    keyboard_thread.start()
    mouse_thread.start()

    try:
        # Keep the main thread alive
        keyboard_thread.join()
        mouse_thread.join()
    except KeyboardInterrupt:
        print("Monitoring stopped")
