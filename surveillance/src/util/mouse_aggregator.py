from datetime import datetime, timezone
from dataclasses import dataclass
from typing import List, Callable

from ..object.classes import PeripheralAggregate


@dataclass
class InProgressAggregation:
    start_time: float
    end_time: float
    event_count: int  # a count of the number of events in the package


class MouseEventAggregator:
    def __init__(self, clock, timeout_ms: int):
        # NOTE: Clock has *absolutely no need* to care about tz, user vs system, etc.
        self.clock = clock
        self.ms_timeout = timeout_ms  # Think 10 or 50

        self.current_aggregation: InProgressAggregation | None = None

    def set_initialization_aggregation(self):
        now = self.clock.now()

        # now, now, [] -> default, as close to meaningless as it gets
        return InProgressAggregation(now, now, 0)

    def add_event(self, timestamp: float) -> None | PeripheralAggregate:
        """A timestamp must be a datetime.timestamp() result."""
        if timestamp is None:
            raise TypeError("Timestamp cannot be None")
        if not isinstance(timestamp, (int, float)):
            raise TypeError("Timestamp must be a number")

        if timestamp > self.clock.now().timestamp():
            raise ValueError("Timestamp cannot be in the future")
        if self.current_aggregation and timestamp < self.current_aggregation.end_time:
            print(timestamp)
            raise ValueError("Timestamps must be in chronological order")

        uninitialized = self.current_aggregation is None
        if uninitialized:
            self.start_new_aggregate(timestamp)
            return None

        if self.current_aggregation is None:
            raise ValueError("None should be impossible here")
        next_added_timestamp_difference = timestamp - \
            self.current_aggregation.end_time
        session_window_has_elapsed = next_added_timestamp_difference > self.ms_timeout
        if session_window_has_elapsed:
            # "If no mouse moves within <timeout_ms> ms, end sesion; report session to db"
            finished_aggregate = self.package_aggregate(
                self.current_aggregation)
            self.start_new_aggregate(timestamp)

            return finished_aggregate

        self.current_aggregation.end_time = timestamp
        self.current_aggregation.event_count += 1
        return None

    def start_new_aggregate(self, timestamp):
        self.current_aggregation = InProgressAggregation(
            timestamp, timestamp, 1)

    def force_complete(self) -> InProgressAggregation | None:
        if not self.current_aggregation:
            return None

        completed = self.current_aggregation
        self.current_aggregation = self.set_initialization_aggregation()

        return completed

    def package_aggregate(self, aggregate: InProgressAggregation) -> PeripheralAggregate:
        """
        Aggregate comes out of this class as start_time, end_time, event_count. 
        """
        start = aggregate.start_time
        end = aggregate.end_time
        return PeripheralAggregate(start, end, aggregate.event_count)
