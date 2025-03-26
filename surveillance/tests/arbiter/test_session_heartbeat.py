
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock

import threading
import time

from src.arbiter.session_heartbeat import KeepAliveEngine

class MockDaoConn:
    def __init__(self):
        pass
        
    def add_ten_sec_to_end_time(self):
        pass

    def deduct_duration(self):
        pass

# Custom sleep function that does nothing
def fast_sleep(_):
    pass


def test_hit_max_window():
    dao_mock = MagicMock()
    add_ten_mock = MagicMock()
    dao_mock.add_ten_sec_to_end_time = add_ten_mock
    session = "test_session"

    greater_than_ten = 11
    exactly_ten = 10
    less_than_ten = 9

    instance = KeepAliveEngine(session, dao_mock)

    # Test the test conditions
    assert instance.max_interval == 10

    instance.elapsed = less_than_ten
    assert instance._hit_max_window() is False
    instance.elapsed = exactly_ten
    assert instance._hit_max_window() is True
    instance.elapsed = greater_than_ten
    assert instance._hit_max_window() is True


def test_iterate_loop():
    dao_mock = MagicMock()
    add_ten_mock = MagicMock()
    dao_mock.add_ten_sec_to_end_time = add_ten_mock
    session = "test_session"

    instance = KeepAliveEngine(session, dao_mock)
    assert instance.elapsed == 0

    instance.iterate_loop()
    assert instance.elapsed == 1

    instance.iterate_loop()
    instance.iterate_loop()
    assert instance.elapsed == 3

    # Ensure _pulse_add_ten() was called at least once
    dao_mock.add_ten_sec_to_end_time.assert_not_called()



def test_running_for_three_sec():
    dao_mock = MagicMock()
    add_ten_mock = MagicMock()
    deduct_duration_mock = MagicMock()
    dao_mock.deduct_duration = deduct_duration_mock
    dao_mock.add_ten_sec_to_end_time = add_ten_mock
    session = "test_session"

    instance = KeepAliveEngine(session, dao_mock)
    assert instance.elapsed == 0

    instance.iterate_loop()
    assert instance.elapsed == 1

    instance.iterate_loop()
    instance.iterate_loop()
    assert instance.elapsed == 3

    add_ten_mock.assert_not_called()
    deduct_duration_mock.assert_not_called()    



def test_multiple_whole_loops():
    dao_mock = MagicMock()
    add_ten_mock = MagicMock()
    deduct_duration_mock = MagicMock()
    dao_mock.deduct_duration = deduct_duration_mock
    dao_mock.add_ten_sec_to_end_time = add_ten_mock
    session = "test_session"

    instance = KeepAliveEngine(session, dao_mock)

    conclude_spy = Mock(side_effect=instance.conclude)
    instance.conclude = conclude_spy

    two_whole_loops = 20
    and_then_some = 3
    total = two_whole_loops + and_then_some

    for i in range(total):
        instance.iterate_loop()


    # Assert
    conclude_spy.assert_not_called
    add_ten_mock.call_count == 2

    # Act again
    instance.conclude()
    remainder = instance.calculate_remaining_window(and_then_some)

    assert 10 - and_then_some == remainder, "Setup conditions not met in test"
    # Assert
    deduct_duration_mock.assert_called_with(remainder, session)  


def test_window_usage_calculation():
    dao_mock = MagicMock()
    add_ten_mock = MagicMock()
    dao_mock.deduct_duration = add_ten_mock
    session = "test_session"

    instance = KeepAliveEngine(session, dao_mock)

    full_window = 10
    used_amt = 3

    remainder = instance.calculate_remaining_window(used_amt)

    assert remainder == full_window - used_amt


def test_conclude():
    dao_mock = MagicMock()
    add_ten_mock = MagicMock()
    dao_mock.deduct_duration = add_ten_mock
    session = "test_session"

    instance = KeepAliveEngine(session, dao_mock)
    instance.iterate_loop()
    assert instance.elapsed == 1

    instance.iterate_loop()
    instance.iterate_loop()
    assert instance.elapsed == 3

    # Act
    instance.conclude()

    assert dao_mock.deduct_duration.call_count == 1
    