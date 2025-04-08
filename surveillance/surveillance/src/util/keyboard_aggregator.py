from datetime import datetime, timezone
from dataclasses import dataclass
from multiprocessing import Value
from typing import List, Callable, Optional, Type

# Import the base and derived classes

from ..object.classes import PeripheralAggregate, KeyboardAggregate, MouseAggregate


@dataclass
class InProgressAggregation:
    start_time: float
    end_time: float
    events: List[float]


class EventAggregator:
    def __init__(self, timeout_ms: int,
                 aggregate_class: Type[PeripheralAggregate] = KeyboardAggregate):
        self.timeout_in_sec = timeout_ms / 1000
        self.current_aggregation: Optional[InProgressAggregation] = None
        self._on_aggregation_complete = None
        # Store which type of aggregate to create
        self.aggregate_class = aggregate_class

    def set_callback(self, callback: Callable):
        self._on_aggregation_complete = callback

    def add_event(self, timestamp: float) -> Optional[List[datetime]]:
        """A timestamp must be a datetime.timestamp() result."""
        if timestamp is None:
            raise TypeError("Timestamp cannot be None")
        if not isinstance(timestamp, (int, float)):
            raise TypeError("Timestamp must be a number")

        # if timestamp > self.user_facing_clock.now().timestamp():
            # raise ValueError("Timestamp cannot be in the future")
        if self.current_aggregation and timestamp < self.current_aggregation.end_time:
            print(timestamp)
            raise ValueError("Timestamps must be in chronological order")

        uninitialized = self.current_aggregation is None
        if uninitialized:
            self.current_aggregation = InProgressAggregation(
                timestamp, timestamp, [timestamp])
            return None
        if self.current_aggregation is None:
            raise ValueError("Should be impossible to get None here")

        next_added_timestamp_difference = timestamp - self.current_aggregation.end_time
        session_window_has_elapsed = next_added_timestamp_difference > self.timeout_in_sec
        if session_window_has_elapsed:
            # "If no keystroke within timeout, end session; report session to db"
            events_in_session = self.current_aggregation.events
            completed_to_report = self.convert_events_to_timestamps(
                events_in_session)

            self.start_new_aggregate(timestamp)

            if self._on_aggregation_complete:
                self._on_aggregation_complete(completed_to_report)
            return completed_to_report

        self.current_aggregation.end_time = timestamp
        self.current_aggregation.events.append(timestamp)
        return None

    def convert_events_to_timestamps(self, current_agg_events):
        return [datetime.fromtimestamp(t, tz=timezone.utc) for t in current_agg_events]

    def start_new_aggregate(self, timestamp):
        self.current_aggregation = InProgressAggregation(
            timestamp, timestamp, [timestamp])

    def force_complete(self) -> Optional[InProgressAggregation]:
        """Used only in stop() and when shutting down"""
        if not self.current_aggregation:
            return None

        completed = self.current_aggregation
        self.current_aggregation = None

        if self._on_aggregation_complete:
            events_as_datetimes = self.convert_events_to_timestamps(
                completed.events)
            self._on_aggregation_complete(events_as_datetimes)

        return completed

    def package_keyboard_events_for_db(self, aggregate: list) -> KeyboardAggregate:
        """
        Aggregate comes out as an array of datetimes. 
        The DB must get an obj with start_time, end_time.
        Uses the configured aggregate_class to determine which type to create.
        """
        start = aggregate[0]
        end = aggregate[-1]
        return KeyboardAggregate(start, end, len(aggregate))

    def package_mouse_events_for_db(self, aggregate: list) -> MouseAggregate:
        """
        Aggregate comes out as an array of datetimes. 
        The DB must get an obj with start_time, end_time.
        Uses the configured aggregate_class to determine which type to create.
        """
        start = aggregate[0]
        end = aggregate[-1]
        return MouseAggregate(start, end, len(aggregate))

    def set_aggregate_class(self, aggregate_class: Type[PeripheralAggregate]):
        """
        Change the type of aggregate being created (e.g., from keyboard to mouse)
        """
        self.aggregate_class = aggregate_class
