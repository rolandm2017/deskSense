# test_aggregator.py
from unittest import BaseTestSuite
import pytest
from typing import List
from dataclasses import dataclass
from datetime import timedelta

from src.util.keyboard_aggregator import EventAggregator, InProgressAggregation

from src.util.clock import SystemClock
from surveillance.tests.mocks.mock_clock import MockClock

####
# Happy path tests
####

system_clock = SystemClock()


def test_new_aggregation_creation():
    aggregator = EventAggregator(system_clock, timeout_ms=1000)
    timestamp = system_clock.now().timestamp()

    result = aggregator.add_event(timestamp)

    assert result is None
    assert aggregator.current_aggregation is not None
    assert aggregator.current_aggregation.start_time == timestamp
    assert aggregator.current_aggregation.end_time == timestamp
    assert aggregator.current_aggregation.events == [timestamp]


def test_events_within_timeout():
    base_time = system_clock.now() - timedelta(seconds=10)

    t1 = system_clock.now() - timedelta(seconds=10)
    t2 = t1 + timedelta(milliseconds=200)
    t3 = t2 + timedelta(milliseconds=212)
    t4 = t3 + timedelta(milliseconds=138)
    times = [t1, t2, t3, t4]
    clock = MockClock(times)

    aggregator = EventAggregator(clock, timeout_ms=1000)
    # so adding time doesn't yield the future
    events = [t1, t2, t3]

    for t in events:
        result = aggregator.add_event(t.timestamp())
        assert result is None

    assert aggregator.current_aggregation is not None
    assert len(aggregator.current_aggregation.events) == 3
    assert aggregator.current_aggregation.start_time == events[0].timestamp()
    assert aggregator.current_aggregation.end_time == events[-1].timestamp()


def test_timeout_creates_new_aggregation(monkeypatch):
    """
    Test that adding a first event, and then a second one
    after a delay greater than that of the timeout, yields a completed event
    """
    # Mock time.time() to return fixed values
    # current_time = 1000000.0
    # FIXME: What is the point of this time stuff?
    now = system_clock.now()
    slightly_earlier = now - timedelta(seconds=2)
    way_earlier = now - timedelta(seconds=5)

    aggregator = EventAggregator(system_clock, timeout_ms=1000)
    base_time = slightly_earlier.timestamp()

    first_result = aggregator.add_event(base_time)
    assert first_result is None

    completed = aggregator.add_event(base_time + 1.8)  # > 1000ms timeout

    assert completed is not None, "Because adding another event, much later, closes the current window"
    assert isinstance(completed, list)
    assert len(completed) == 1
    assert completed[0].timestamp() == base_time


def test_callback_execution(monkeypatch):
    # current_time = 1000000.0
    # monkeypatch.setattr('time.time', lambda: current_time)
    current_time = system_clock.now()
    earlier_than_system_time = current_time - timedelta(seconds=3)
    slightly_later = earlier_than_system_time + timedelta(seconds=2)

    callback_executed = False
    completed_aggregation = None

    def callback(agg):
        nonlocal callback_executed, completed_aggregation
        callback_executed = True
        completed_aggregation = agg

    aggregator = EventAggregator(system_clock, timeout_ms=1000)
    aggregator.set_callback(callback)

    aggregator.add_event(earlier_than_system_time.timestamp())
    aggregator.add_event(slightly_later.timestamp())

    assert callback_executed
    assert completed_aggregation is not None
    assert len(completed_aggregation) == 1


def test_force_complete():
    aggregator = EventAggregator(system_clock, timeout_ms=1000)
    now = system_clock.now()
    t1 = now - timedelta(seconds=10)
    t2 = now - timedelta(seconds=9.8)
    t3 = now - timedelta(seconds=9.6)
    events = [t1, t2, t3]

    for t in events:
        aggregator.add_event(t.timestamp())

    completed = aggregator.force_complete()

    assert completed is not None
    assert len(completed.events) == 3
    assert completed.start_time == events[0].timestamp()
    assert completed.end_time == events[-1].timestamp()

    # ### It reset correctly
    assert aggregator.current_aggregation is not None
    current_time = system_clock.now().timestamp()
    time_difference = abs(
        aggregator.current_aggregation.start_time - current_time)

    # Assert that the difference is less than a small threshold (e.g., 0.1 seconds)
    assert time_difference < 0.01, f"Timestamp {aggregator.current_aggregation.start_time} is too far from current time {current_time}"

    # Same for end_time
    time_difference = abs(
        aggregator.current_aggregation.end_time - current_time)
    assert time_difference < 0.01

    assert len(aggregator.current_aggregation.events) == 0


def test_force_complete_empty():
    aggregator = EventAggregator(system_clock, timeout_ms=1000)
    completed = aggregator.force_complete()
    assert completed is None


def test_callback_on_force_complete():
    callback_executed = False

    def callback(agg):
        nonlocal callback_executed
        callback_executed = True

    aggregator = EventAggregator(system_clock, timeout_ms=1000)
    aggregator.set_callback(callback)

    aggregator.add_event(system_clock.now().timestamp())
    aggregator.force_complete()

    assert callback_executed

####
# Sad path tests
####


def test_invalid_timestamp_type():
    aggregator = EventAggregator(system_clock, timeout_ms=1000)
    with pytest.raises(TypeError, match="Timestamp must be a number"):
        aggregator.add_event("not a timestamp")  # type: ignore


def test_none_timestamp():
    aggregator = EventAggregator(system_clock, timeout_ms=1000)
    with pytest.raises(TypeError, match="Timestamp cannot be None"):
        aggregator.add_event(None)  # type: ignore


def test_future_timestamp():
    aggregator = EventAggregator(system_clock, timeout_ms=1000)
    future_time = system_clock.now() + timedelta(hours=1)
    with pytest.raises(ValueError, match="Timestamp cannot be in the future"):
        aggregator.add_event(future_time.timestamp())


def test_out_of_order_timestamps():
    aggregator = EventAggregator(system_clock, timeout_ms=1000)
    base_time = system_clock.now()

    submitted_time = base_time - timedelta(seconds=20)

    later = submitted_time + timedelta(seconds=1)

    much_much_earlier = base_time - timedelta(seconds=60)

    aggregator.add_event(later.timestamp())
    with pytest.raises(ValueError):
        aggregator.add_event(much_much_earlier.timestamp()
                             )  # Earlier timestamp
