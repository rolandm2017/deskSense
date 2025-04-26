import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

from .mock_clock import MockClock

import unittest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from surveillance.src.util.time_wrappers import UserLocalTime
from .mock_clock import UserLocalTimeMockClock

class TestMockClock(unittest.TestCase):
    def test_counter_increment(self):
        """Test that the counter increments exactly once per call to now()."""
        # Create a list of 20 UserLocalTime objects
        times = [
            UserLocalTime(datetime(2025, 3, 22, 16, 14, i, tzinfo=timezone.utc))
            for i in range(20)
        ]
        
        # Create our mock clock
        clock = UserLocalTimeMockClock(times)
        
        # Call now() 6 times and verify the counter
        for i in range(6):
            result = clock.now()
            self.assertEqual(clock.count_of_times, i + 1, 
                            f"Counter should be {i+1} after {i+1} calls, but got {clock.count_of_times}")
        
        # This should be call #7
        result = clock.now()
        self.assertEqual(clock.count_of_times, 7, "Counter should be 7 after 7 calls")
        
        # This should be call #8
        result = clock.now()
        self.assertEqual(clock.count_of_times, 8, "Counter should be 8 after 8 calls")
        
        # This should be call #9
        result = clock.now()
        self.assertEqual(clock.count_of_times, 9, "Counter should be 9 after 9 calls")
        
        # This should be call #10
        result = clock.now()
        self.assertEqual(clock.count_of_times, 10, "Counter should be 10 after 10 calls")
    
    def test_counter_with_thread(self):
        """Test counter behavior with a thread that also calls the clock."""
        import threading
        import time
        
        # Create a list of 20 UserLocalTime objects
        times = [
            UserLocalTime(datetime(2025, 3, 22, 16, 14, i, tzinfo=timezone.utc))
            for i in range(20)
        ]
        
        # Create our mock clock
        clock = UserLocalTimeMockClock(times)
        
        # Define a function that will run in a separate thread
        def background_calls():
            # Make 3 calls from the background thread
            for _ in range(3):
                clock.now()
                time.sleep(0.01)  # Small delay
        
        # Start the background thread
        thread = threading.Thread(target=background_calls)
        thread.start()
        
        # Make 5 calls from the main thread
        for i in range(5):
            result = clock.now()
            time.sleep(0.01)  # Small delay
        
        # Wait for the background thread to finish
        thread.join()
        
        # We should have made a total of 8 calls (5 main + 3 background)
        self.assertEqual(clock.count_of_times, 8, 
                         f"Expected 8 total calls but got {clock.count_of_times}")
    
    def test_today_start_behavior(self):
        """Test that today_start() doesn't cause counter issues."""
        # Create a list of UserLocalTime objects
        times = [
            UserLocalTime(datetime(2025, 3, 22, 16, 14, i, tzinfo=timezone.utc))
            for i in range(10)
        ]
        
        # Create our mock clock
        clock = UserLocalTimeMockClock(times)
        
        # Call now() a few times
        for i in range(3):
            result = clock.now()
        
        # Current counter should be 3
        self.assertEqual(clock.count_of_times, 3)
        
        # Call today_start() when _current_time is already set
        start_of_day = clock.today_start()
        
        # Counter should still be 3 (if today_start uses existing _current_time)
        self.assertEqual(clock.count_of_times, 3, 
                         "today_start() shouldn't increment counter when _current_time exists")
        
        # Set _current_time to None and call today_start again
        clock._current_time = None
        start_of_day = clock.today_start()
        
        # Counter should be 4 (today_start should call now() once)
        self.assertEqual(clock.count_of_times, 4, 
                         "today_start() should increment counter exactly once when calling now()")



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
