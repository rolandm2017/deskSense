# linux_api.py
import zmq

import zmq
import json
from datetime import datetime


import os
from dotenv import load_dotenv


load_dotenv()


# In the peripheral detector

# Setup ZMQ publisher
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://127.0.0.1:5555")

# Replace your POST functions


def publish_keyboard_event():
    event = {
        "type": "keyboard",
        "timestamp": datetime.now().isoformat()
    }
    socket.send_json(event)


def publish_mouse_events(aggregate):
    print("Publishing", aggregate["start"])
    event = {
        "type": "mouse",
        "start": aggregate["start"].isoformat(),  # MUST be isoformat
        "end": aggregate["end"].isoformat()
    }
    socket.send_json(event)
