import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

from .mock_clock import MockClock


def test_using_list_mins():
    times = [
        datetime(2024, 1, 1, 12, 0),  # noon
        datetime(2024, 1, 1, 12, 1),  # 1pm
        datetime(2024, 1, 1, 12, 2),   # 2pm
        datetime(2024, 1, 1, 12, 3),   # 2pm
        datetime(2024, 1, 1, 12, 4),   # 2pm
    ]

    clock = MockClock(times)

    assert clock.now().minute == 0
    assert clock.now().minute == 1
    assert clock.now().minute == 2
    assert clock.now().minute == 3
    assert clock.now().minute == 4


def test_using_list_hours():
    times = [
        datetime(2024, 1, 1, 12, 0),  # noon
        datetime(2024, 1, 1, 13, 1),  # 1pm
        datetime(2024, 1, 1, 14, 2),   # 2pm
        datetime(2024, 1, 1, 15, 3),   # 2pm
        datetime(2024, 1, 1, 16, 4),   # 2pm
    ]

    clock = MockClock(times)

    assert clock.now().hour == 12
    assert clock.now().hour == 13
    assert clock.now().hour == 14
    assert clock.now().hour == 15
    assert clock.now().hour == 16


def test_using_iterator_hours():
    def time_generator():
        current = datetime(2024, 1, 1)
        while True:
            yield current
            current += timedelta(hours=1)

    clock = MockClock(time_generator())

    assert clock.now().hour == 0
    assert clock.now().hour == 1
    assert clock.now().hour == 2
    assert clock.now().hour == 3
    assert clock.now().hour == 4


def test_using_iterator_minutes():
    def time_generator():
        current = datetime(2024, 1, 1)
        while True:
            yield current
            current += timedelta(minutes=1)

    clock = MockClock(time_generator())

    assert clock.now().minute == 0
    assert clock.now().minute == 1
    assert clock.now().minute == 2
    assert clock.now().minute == 3
    assert clock.now().minute == 4


def test_advance_time():
    times = [
        datetime(2024, 1, 1, 12, 0),  # noon
        datetime(2024, 1, 1, 12, 2),  # 12:02
        datetime(2024, 1, 1, 12, 4),  # 12:04
        datetime(2024, 1, 1, 13, 6),  # 1:06
        datetime(2024, 1, 1, 13, 24),  # 1:24
        datetime(2024, 1, 1, 14, 33),  # 1:33
        datetime(2024, 1, 1, 16, 3),
        datetime(2024, 1, 1, 16, 4),  # skip 1
        datetime(2024, 1, 1, 16, 5),  # skip 2
        datetime(2024, 1, 1, 16, 6),  # skip 3
        datetime(2024, 1, 1, 16, 7),  # skip 4
        datetime(2024, 1, 1, 16, 8),  # skip 5
        datetime(2024, 1, 1, 23, 59),
    ]

    clock = MockClock(times)

    t1 = clock.now()
    assert t1.hour == 12 and t1.minute == 0
    t2 = clock.now()
    assert t2.hour == 12 and t2.minute == 2

    clock.advance_time(2)

    t3 = clock.now()

    assert t3.hour == 13 and t3.minute == 24

    clock.advance_time(1)

    t4 = clock.now()

    assert t4.hour == 16 and t4.minute == 3

    clock.advance_time(5)

    t5 = clock.now()

    assert t5.hour == 23 and t5.minute == 59
