# test_timeline_aggregator.py
import pytest
from time import time
from typing import List
from dataclasses import dataclass

from surveillance.src.util.timeline_event_aggregator import aggregate_timeline_events

# given these -- directly from the real db
from ..data.timeline_data import all_mouse_events, all_keyboard_events


def test_aggregate_timeline_events():
    # arrange
    batch = all_mouse_events
    threshold = 1000  # one sec
    # act
    grouped = aggregate_timeline_events(batch, threshold=threshold)

    # assert
    # NOTE: I *ONLY* put in data and assumed it works. Data came direct from read_day_mice
    assert len(grouped) == 1  # 0 gaps of longer than 1,000 ms
    for entry in grouped:
        assert entry.start is not None, "A timestamp was missing"
        assert entry.end is not None, "An ending timestamp was missing"
    for i in range(0, len(grouped) - 1):
        start = grouped[i + 1]
        end = grouped[i]

        time_delta = end.end - start.start
        milliseconds = time_delta.total_seconds() * 1000
        assert milliseconds < threshold, f"Time difference {milliseconds}ms exceeds threshold of {threshold}ms"
        delta = (grouped[i].end.timestamp() -
                 grouped[i + 1].start.timestamp()) * 1000
        assert delta < threshold


def test_aggregate_timeline_events_again():
    # arrange
    batch = all_keyboard_events
    threshold = 1000  # one sec
    # act
    grouped = aggregate_timeline_events(batch, threshold=threshold)
    # assert
    # NOTE: I *ONLY* put in data and assumed it works. Data came direct from read_day_keyboard
    assert len(grouped) == 2  # 1 gaps of longer than 1,000 ms
    for entry in grouped:
        assert entry.start is not None, "A timestamp was missing"
        assert entry.end is not None, "An ending timestamp was missing"
    for i in range(0, len(grouped) - 1):
        start = grouped[i + 1]
        end = grouped[i]
        assert start is not None, "Testing my tests"  # testing my tests
        assert end is not None, "Testing my tests"
        assert start.start is not None, "Testing tests"

        time_delta = end.end - start.start
        milliseconds = time_delta.total_seconds() * 1000
        assert milliseconds < threshold, f"Time difference {milliseconds}ms exceeds threshold of {threshold}ms"
