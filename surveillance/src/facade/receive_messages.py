# In your main application
import zmq
import json
from datetime import datetime

from .facade_singletons import get_keyboard_facade_instance, get_mouse_facade_instance

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://127.0.0.1:5555")
socket.setsockopt_string(zmq.SUBSCRIBE, "")  # Subscribe to all messages

keyboard_facade = get_keyboard_facade_instance()
mouse_facade = get_mouse_facade_instance()

# Process messages
while True:
    message = socket.recv_json()
    try:
        if isinstance(message, bytes):
            event = json.loads(message.decode('utf-8'))
        elif isinstance(message, str):
            event = json.loads(message)
        else:
            # It might already be deserialized
            event = message

        # Now process the event
        if isinstance(event, dict) and "type" in event:
            if event["type"] == "keyboard" and "timestamp" in event:
                iso_string = str(event["timestamp"])
                converted_datetime = datetime.fromisoformat(iso_string)
                keyboard_facade.add_event(converted_datetime)
            elif event["type"] == "mouse":
                # Event is a dict containing:
                # "start": aggregate["start"].isoformat(),
                # "end": aggregate["end"].isoformat()
                print(event, "38ru")
                event_dict = {
                    "start": event["start"],
                    "end": event["end"]
                }

                mouse_facade.add_event(event_dict)  # type: ignore
        else:
            print(f"Received unexpected message format: {type(event)}")
            print(f"Message content: {event}")
    except json.JSONDecodeError:
        print("Failed to decode JSON from message:", message)
    except Exception as e:
        print(f"Error processing message: {e}")
