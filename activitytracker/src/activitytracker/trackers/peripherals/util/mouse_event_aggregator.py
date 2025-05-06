
import threading
from datetime import datetime

from activitytracker.object.classes import MouseAggregate


class MouseEventAggregator:
    """Really just a named array; the timer will take place outside of it, or else timers are duplicated"""

    def __init__(self):
        self.current_aggregation = []
        self.count = 0

    def add_event(self) -> None | MouseAggregate:
        """A timestamp must be a datetime.timestamp() result."""
        next = self.count + 1
        self.count += 1
        self.current_aggregation.append(next)

    def package_aggregate(self):
        return self.current_aggregation
        # """
        # Aggregate comes out of this class as start_time, end_time, event_count.
        # """
        # start = aggregate.start_time
        # end = aggregate.end_time
        # return MouseAggregate(start, end, aggregate.event_count)

    def reset(self):
        self.current_aggregation = []
        self.count = 0
