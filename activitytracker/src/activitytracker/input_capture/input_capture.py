import json
import os

from datetime import datetime, timedelta

from typing import TypedDict

from activitytracker.object.classes import ProgramSession


def get_timestamp_string():
    """Returns current time as YYYY-MM-DD_HH-MM-SS string for file naming."""
    now = datetime.now()
    return now.strftime("%Y-%m-%d_%H-%M-%S")


class MetadataDict(TypedDict):
    source: str
    collection_method: str
    time: str  # ISO string


class InputCaptureDict(TypedDict):
    type: str
    data: ProgramSession
    metadata: MetadataDict


class EventEncoder(json.JSONEncoder):
    def default(self, obj):
        # Handle ProgramSession, ActivitySession, and other custom objects
        if hasattr(obj, "__dict__"):
            # Convert object to dictionary, excluding special attributes
            obj_dict = {k: v for k, v in obj.__dict__.items() if not k.startswith("__")}

            # Add the class name to make deserialization easier later
            obj_dict["__class__"] = obj.__class__.__name__

            return obj_dict

        # Handle datetime objects
        elif isinstance(obj, datetime):
            return obj.isoformat()

        # Handle timedelta objects
        elif isinstance(obj, timedelta):
            return {"__timedelta__": True, "total_seconds": obj.total_seconds()}

        # Handle ZoneInfo objects
        elif obj.__class__.__name__ == "ZoneInfo":
            return {"__zoneinfo__": True, "key": str(obj)}

        # Handle UserLocalTime objects (if they don't have __dict__)
        elif hasattr(obj, "__class__") and obj.__class__.__name__ == "UserLocalTime":
            # You might need to customize this based on your UserLocalTime implementation
            return {
                "__userlocal__": True,
                "datetime": obj.datetime.isoformat(),
                "timezone": str(obj.tzinfo) if hasattr(obj, "tzinfo") else None,
            }

        # Let the base class handle other types or raise TypeError
        return json.JSONEncoder.default(self, obj)


class InputCapture:
    def __init__(self) -> None:
        self.events = []
        logs_dir = os.path.join(".", "logs")
        os.makedirs(logs_dir, exist_ok=True)

        # Save to logs directory with .json extension
        self.filename = os.path.join(
            logs_dir, "input_from_" + get_timestamp_string() + ".json"
        )

    def capture_if_active(self, event: ProgramSession):
        print("Capturing event")
        self.events.append(event)

    def log_to_output_file(self):
        # Create a custom encoder if your objects have __str__ but not a standard JSON representation

        # Write to the file using the custom encoder
        with open(self.filename, "w") as f:
            json.dump(self.events, f, cls=EventEncoder, indent=4)
