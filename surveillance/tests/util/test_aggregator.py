# test_aggregator.py
import pytest
from time import time
from typing import List
from dataclasses import dataclass

from surveillance.src.util.aggregator import EventAggregator, InProgressAggregation

####
# Happy path tests
####


def test_new_aggregation_creation():
    aggregator = EventAggregator(timeout_ms=1000)
    timestamp = time()

    result = aggregator.add_event(timestamp)

    assert result is None
    assert aggregator.current_aggregation is not None
    assert aggregator.current_aggregation.start_time == timestamp
    assert aggregator.current_aggregation.end_time == timestamp
    assert aggregator.current_aggregation.events == [timestamp]


def test_events_within_timeout():
    aggregator = EventAggregator(timeout_ms=1000)
    base_time = time()
    events = [base_time, base_time + 0.5, base_time + 0.8]

    for t in events:
        result = aggregator.add_event(t)
        assert result is None

    assert len(aggregator.current_aggregation.events) == 3
    assert aggregator.current_aggregation.start_time == events[0]
    assert aggregator.current_aggregation.end_time == events[-1]


def test_timeout_creates_new_aggregation(monkeypatch):
    # Mock time.time() to return fixed values
    current_time = 1000000.0
    monkeypatch.setattr('time.time', lambda: current_time)

    aggregator = EventAggregator(timeout_ms=1000)
    base_time = current_time

    aggregator.add_event(base_time)
    completed = aggregator.add_event(base_time + 1.8)  # > 1000ms timeout

    assert completed is not None
    assert len(completed) == 1
    assert isinstance(completed, list)
    assert completed[0].timestamp() == base_time
    assert completed[0].timestamp() == base_time


def test_callback_execution(monkeypatch):
    current_time = 1000000.0
    monkeypatch.setattr('time.time', lambda: current_time)

    callback_executed = False
    completed_aggregation = None

    def callback(agg):
        nonlocal callback_executed, completed_aggregation
        callback_executed = True
        completed_aggregation = agg

    aggregator = EventAggregator(timeout_ms=1000)
    aggregator.set_callback(callback)

    aggregator.add_event(current_time)
    aggregator.add_event(current_time + 2.0)

    assert callback_executed
    assert completed_aggregation is not None
    print(completed_aggregation, '73ru')
    assert len(completed_aggregation) == 1


def test_force_complete():
    aggregator = EventAggregator(timeout_ms=1000)
    base_time = time()
    events = [base_time, base_time + 0.1, base_time + 0.2]

    for t in events:
        aggregator.add_event(t)

    completed = aggregator.force_complete()

    assert completed is not None
    assert len(completed.events) == 3
    assert completed.start_time == events[0]
    assert completed.end_time == events[-1]
    assert aggregator.current_aggregation is None


def test_force_complete_empty():
    aggregator = EventAggregator(timeout_ms=1000)
    completed = aggregator.force_complete()
    assert completed is None


def test_callback_on_force_complete():
    callback_executed = False

    def callback(agg):
        nonlocal callback_executed
        callback_executed = True

    aggregator = EventAggregator(timeout_ms=1000)
    aggregator.set_callback(callback)

    aggregator.add_event(time())
    aggregator.force_complete()

    assert callback_executed

####
# Sad path tests
####


def test_negative_timeout():
    with pytest.raises(ValueError):
        EventAggregator(timeout_ms=-1000)


def test_zero_timeout():
    with pytest.raises(ValueError):
        EventAggregator(timeout_ms=0)


def test_invalid_timestamp_type():
    aggregator = EventAggregator(timeout_ms=1000)
    with pytest.raises(TypeError):
        aggregator.add_event("not a timestamp")


def test_none_timestamp():
    aggregator = EventAggregator(timeout_ms=1000)
    with pytest.raises(TypeError):
        aggregator.add_event(None)


def test_future_timestamp():
    aggregator = EventAggregator(timeout_ms=1000)
    future_time = time() + 3600  # 1 hour in future
    with pytest.raises(ValueError):
        aggregator.add_event(future_time)


def test_out_of_order_timestamps():
    aggregator = EventAggregator(timeout_ms=1000)
    base_time = time()

    aggregator.add_event(base_time + 1.0)
    with pytest.raises(ValueError):
        aggregator.add_event(base_time)  # Earlier timestamp
