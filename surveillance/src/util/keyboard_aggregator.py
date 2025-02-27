from datetime import datetime
from dataclasses import dataclass
from time import time
from typing import List, Callable

from ..object.classes import KeyboardAggregate


@dataclass
class InProgressAggregation:
    start_time: float
    end_time: float
    events: List[float]


class EventAggregator:
    def __init__(self, timeout_ms: int):
        if timeout_ms <= 0:
            raise ValueError("Timeout must be positive")
        self.timeout = timeout_ms / 1000
        self.current_aggregation: InProgressAggregation = None
        self._on_aggregation_complete = None

    def set_callback(self, callback: Callable):  # function
        self._on_aggregation_complete = callback

    def add_event(self, timestamp: float):
        """A timestamp must be a datetime.timestamp() result."""
        if not isinstance(timestamp, (int, float)):
            raise TypeError("Timestamp must be a number")
        if timestamp is None:
            raise TypeError("Timestamp cannot be None")
        if timestamp > time() + 1:  # 1 second buffer for clock skew
            raise ValueError("Timestamp cannot be in the future")
        if self.current_aggregation and timestamp < self.current_aggregation.end_time:
            raise ValueError("Timestamps must be in chronological order")

        uninitialized = not self.current_aggregation
        if uninitialized:
            self.current_aggregation = InProgressAggregation(
                timestamp, timestamp, [timestamp])
            return None

        next_added_timestamp_difference = timestamp - self.current_aggregation.end_time
        session_window_has_elapsed = next_added_timestamp_difference > self.timeout
        if session_window_has_elapsed:
            # "If no keystroke within 300 ms, end sesion; report session to db"
            events_in_session = self.current_aggregation.events
            completed_to_report = self.convert_events_to_timestamps(events_in_session
                                                                    )
            #
            # "Completed report" will be used to, um, get the first and last entry,
            # to see "start_time", "end_time"
            #

            self.start_new_aggregate(timestamp)

            if self._on_aggregation_complete:
                self._on_aggregation_complete(completed_to_report)
            return completed_to_report

        self.current_aggregation.end_time = timestamp
        self.current_aggregation.events.append(timestamp)
        return None

    def convert_events_to_timestamps(self, current_agg_events):
        return [datetime.fromtimestamp(t) for t in current_agg_events]

    def start_new_aggregate(self, timestamp):
        self.current_aggregation = InProgressAggregation(
            timestamp, timestamp, [timestamp])

    def force_complete(self):
        if not self.current_aggregation:
            return None

        completed = self.current_aggregation
        self.current_aggregation = None

        if self._on_aggregation_complete:
            self._on_aggregation_complete(completed)
        return completed

    def package_aggregate_for_db(self, aggregate: list) -> KeyboardAggregate:
        """
        Aggregate comes out as an array of datetimes. 
        The DB must get an obj with start_time, end_time.
        """
        start = aggregate[0]
        end = aggregate[-1]
        return KeyboardAggregate(start, end, len(aggregate))


# # Example usage:
# def on_session_complete(session: Aggregation):
#     print(f"Session completed: {len(session.events)} events")
#     print(f"Duration: {session.end_time - session.start_time:.2f}s")

# grouper = EventAggregator(timeout_ms=1000)
# grouper.set_callback(on_session_complete)

# # Simulate events
# events = [time(), time() + 0.2, time() + 0.4, time() + 2.0]
# for t in events:
#     grouper.add_event(t)

# # Force complete any remaining session
# grouper.force_complete()
