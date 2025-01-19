from dataclasses import dataclass
from time import time
from typing import List

@dataclass
class Aggregation:
    start_time: float
    end_time: float
    events: List[float]

class EventAggregator:
    def __init__(self, timeout_ms: int):
        if timeout_ms <= 0:
            raise ValueError("Timeout must be positive")
        self.timeout = timeout_ms / 1000
        self.current_aggregation = None
        self._on_aggregation_complete = None
    
    def set_callback(self, callback):
        self._on_aggregation_complete = callback
    
    def add_event(self, timestamp: float):
        if not isinstance(timestamp, (int, float)):
            raise TypeError("Timestamp must be a number")
        if timestamp is None:
            raise TypeError("Timestamp cannot be None")
        if timestamp > time() + 1:  # 1 second buffer for clock skew
            print(timestamp, '28ru')
            raise ValueError("Timestamp cannot be in the future")
            
        if self.current_aggregation and timestamp < self.current_aggregation.end_time:
            raise ValueError("Timestamps must be in chronological order")
        
        if not self.current_aggregation:
            self.current_aggregation = Aggregation(timestamp, timestamp, [timestamp])
            return None

        next_added_timestamp_difference = timestamp - self.current_aggregation.end_time 
        if next_added_timestamp_difference > self.timeout:
            completed = self.current_aggregation
            self.current_aggregation = Aggregation(timestamp, timestamp, [timestamp])
            
            if self._on_aggregation_complete:
                self._on_aggregation_complete(completed)
            return completed
            
        self.current_aggregation.end_time = timestamp
        self.current_aggregation.events.append(timestamp)
        return None
    
    def force_complete(self):
        if not self.current_aggregation:
            return None
            
        completed = self.current_aggregation
        self.current_aggregation = None
        
        if self._on_aggregation_complete:
            self._on_aggregation_complete(completed)
        return completed

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