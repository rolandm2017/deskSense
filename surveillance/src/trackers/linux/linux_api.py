# New way
import requests
from requests.exceptions import RequestException


import os
from dotenv import load_dotenv

from ...object.classes import PeripheralAggregate


load_dotenv()

server_endpoint = os.getenv("PATH_TO_PERIPHERALS_ENDPOINT")

if server_endpoint is None:
    raise ValueError("Failed to load DeskSense peripherals endpoint")

keyboard_endpoint = server_endpoint + "/tracker/keyboard"
mouse_endpoint = server_endpoint + "/tracker/mouse"


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


def post_mouse_events(aggregate: PeripheralAggregate):
    """
    Send an empty POST request when a keyboard event is detected.

    Assumes the program will always be informing 
    another program on the same machine, < 1.00 milliseconds away.
    """
    try:
        payload = {
            "start_time": aggregate.start_time,
            "end_time": aggregate.end_time,
            "count": aggregate.count
        }
        response = requests.post(mouse_endpoint, json=payload)

        # Optional: Check if the request was successful
        if response.status_code == 200:
            print("POST request successful")
        else:
            # TODO: Log the failure
            print(
                f"POST request failed with status code: {response.status_code}")

    except RequestException as err:
        print(f"POST request error: {err}")
