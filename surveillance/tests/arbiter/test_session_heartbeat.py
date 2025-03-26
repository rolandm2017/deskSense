
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock

import threading
import time

from src.arbiter.session_heartbeat import SessionHeartbeat

class MockDaoConn:
    def __init__(self):
        pass
        
    def add_ten_sec_to_end_time(self):
        pass

    def deduct_duration(self):
        pass

def test_start():
    session = {}
    dao_conn = MockDaoConn()
    instance = SessionHeartbeat(session, dao_conn)

    # Act
    instance.start()

    # Assert
    assert instance.is_running is True

    # Clean up
    instance.stop()

def test_stop():
    session = {}
    dao_conn = MockDaoConn()
    instance = SessionHeartbeat(session, dao_conn)

    instance.start()
    # Act
    instance.stop()

    # Assert
    assert instance.is_running is False
    

def test_hit_max_window():
    greater_than_ten = 11
    exactly_ten = 10
    less_than_ten = 9

    instance = SessionHeartbeat()

    # Test the test conditions
    assert instance.max_interval == 10

    assert instance._hit_max_window(less_than_ten) is False
    assert instance._hit_max_window(exactly_ten) is True
    assert instance._hit_max_window(greater_than_ten) is True


def test_heartbeat_pulses_without_waiting(self):
    dao_mock = MagicMock()
    add_ten_mock = MagicMock()
    dao_mock.add_ten_sec_to_end_time = add_ten_mock
    session = "test_session"
    
    # Custom sleep function that doesn't actually delay
    def fast_sleep(_):
        pass

    instance = SessionHeartbeat(session, dao_mock, sleep_fn=fast_sleep)
    instance.start()
    
    # Simulate the heartbeat running briefly
    time.sleep(0.1)  # Let thread process
    
    instance.stop()

    # Ensure _pulse_add_ten() was called at least once
    dao_mock.add_ten_sec_to_end_time.assert_called()



def test_running_for_three_sec():
    dao_mock = MagicMock()
    session = "test_session"

    # Custom sleep function that does nothing
    def fast_sleep(_):
        pass

    heartbeat = SessionHeartbeat(session, dao_mock, sleep_fn=fast_sleep)

    # Run _run_heartbeat in a separate thread
    thread = threading.Thread(target=heartbeat._run_heartbeat)
    thread.start()

    # Let it run for 3 loops
    while heartbeat._loop_count < 3:
        time.sleep(0.01)  # Give thread some time to process

    heartbeat.stop()
    thread.join()

    # Assert that it looped exactly 3 times
    assert heartbeat._loop_count == 3



def test_early_termination(self):
    dao_mock = MagicMock()
    add_ten_mock = MagicMock()
    dao_mock.deduct_duration = add_ten_mock
    session = "test_session"
    def fast_sleep(_):
            pass

    instance = SessionHeartbeat(session, dao_mock, sleep_fn=fast_sleep)
    instance.start()
    
    # Run three times
    time.sleep(0.1)  

    # Stop early
    instance.stop()

    # Assert
    assert dao_mock.deduct_duration.called_once
    assert dao_mock.deduct_duration.called_with(10 - 3)

    