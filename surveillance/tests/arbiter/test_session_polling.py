
import pytest
from unittest.mock import AsyncMock, patch, Mock

import asyncio

import threading
import time

from surveillance.src.config.definitions import keep_alive_pulse_delay, window_push_length
from surveillance.src.object.classes import ProgramSession
from surveillance.src.arbiter.session_polling import KeepAliveEngine

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


def test_window_deduction_math():
    dao_mock = Mock()
    
    add_ten_mock = Mock() 
    dao_mock.add_ten_sec_to_end_time = add_ten_mock
    
    deduct_duration_spy = Mock()
    dao_mock.deduct_duration = deduct_duration_spy
    
    session = ProgramSession()

    # The program opens a new window. Ten sec remain
    remaining_sec = 10 
    instance = KeepAliveEngine(session, dao_mock)

    assert instance.calculate_remaining_window(0) == 10
    assert instance.calculate_remaining_window(1) == 9
    assert instance.calculate_remaining_window(5) == 5
    assert instance.calculate_remaining_window(9) == 1
    assert instance.calculate_remaining_window(10) == 0

    # Loops twice, using 2 sec
    used_amount = 2
    remainder = 10 - 2  # 8 remains.

    instance.iterate_loop()
    instance.iterate_loop()

    # The Engine concludes:
    instance.conclude()

    # So deduct_duration was called with the remainder:
    deduct_duration_spy.assert_called_once_with(remainder, session)

    deduct_duration_spy.reset_mock()

    # The program opens a new window. Ten sec remain
    remaining_sec = 10 
    instance = KeepAliveEngine(session, dao_mock)

    # Loops 0 times before concluding.
    instance.conclude()

    # Everything is deducted:
    deduct_duration_spy.assert_called_once_with(remaining_sec, session)

    deduct_duration_spy.reset_mock()

    # The program opens a new window. Ten sec remain
    remaining_sec = 10 
    instance = KeepAliveEngine(session, dao_mock)

    for i in range(0, 17):
        instance.iterate_loop()

    instance.conclude()

    # The program has used 7 sec of the window. 17 % 10 = 7
    used_amount = 7
    remainder = 10 - used_amount

    # The second call to deduction is our remainder:

    deduct_duration_spy.assert_called_once()
    assert deduct_duration_spy.call_args_list[0][0][0] == remainder



def test_hit_max_window():
    dao_mock = Mock()
    add_ten_mock = Mock()
    dao_mock.add_ten_sec_to_end_time = add_ten_mock
    session = ProgramSession()

    greater_than_ten = 11
    exactly_ten = 10
    less_than_ten = 9

    instance = KeepAliveEngine(session, dao_mock)

    # Test the test conditions
    assert instance.max_interval == keep_alive_pulse_delay

    instance.amount_used = less_than_ten
    assert instance._hit_max_window() is False
    instance.amount_used = exactly_ten
    assert instance._hit_max_window() is True
    instance.amount_used = greater_than_ten
    assert instance._hit_max_window() is True


def test_keep_alive_pulse_timing():
    """Test the timing of pulses"""
    mock_recorder = Mock()
    session = ProgramSession("TestApp")
    engine = KeepAliveEngine(session, mock_recorder)
    
    # No pulses at start
    assert mock_recorder.add_ten_sec_to_end_time.call_count == 0
    
    # Iterate 9 times (not enough for pulse)
    for _ in range(9):
        engine.iterate_loop()
    assert mock_recorder.add_ten_sec_to_end_time.call_count == 0
    
    # One more iteration should trigger a pulse
    engine.iterate_loop()
    assert mock_recorder.add_ten_sec_to_end_time.call_count == 1
    
    # Counter should reset
    assert engine.get_amount_used() == 0
    
    # 10 more iterations should trigger another pulse
    for _ in range(10):
        engine.iterate_loop()
    assert mock_recorder.add_ten_sec_to_end_time.call_count == 2


def test_iterate_loop():
    dao_mock = Mock()
    add_ten_mock = Mock()
    deduct_duration_mock = Mock()
    dao_mock.add_ten_sec_to_end_time = add_ten_mock
    dao_mock.deduct_duration = deduct_duration_mock
    session = ProgramSession()
    


    instance = KeepAliveEngine(session, dao_mock)

    pulse_add_ten_spy = Mock(side_effect=instance._pulse_add_ten)
    instance._pulse_add_ten = pulse_add_ten_spy

    assert instance.amount_used == 0  # seconds

    instance.iterate_loop()
    assert instance.amount_used == 1  # seconds

    instance.iterate_loop()
    instance.iterate_loop()
    assert instance.amount_used == 3  # seconds

    # Ensure _pulse_add_ten() was called at least once
    dao_mock.add_ten_sec_to_end_time.assert_not_called()

    # Check what happens when iterate loop elapses the max interval
    max_interval = instance.max_interval

    start_of_4th_loop = 3 + 1
    end_of_9th_loop = max_interval  # max_int is 10, so range(x, 10) takes us to 9
    for i in range(start_of_4th_loop, end_of_9th_loop):
        instance.iterate_loop()
        assert instance.amount_used == i
    
    instance.iterate_loop()

    assert instance.amount_used == 0  # The counter reset

    pulse_add_ten_spy.assert_called_once()
    deduct_duration_mock.assert_not_called()

    add_ten_mock.assert_called_once_with(session)


def test_running_for_three_sec():
    dao_mock = Mock()
    add_ten_mock = Mock()
    deduct_duration_mock = Mock()
    dao_mock.add_ten_sec_to_end_time = add_ten_mock
    dao_mock.deduct_duration = deduct_duration_mock
    session = ProgramSession()
    

    instance = KeepAliveEngine(session, dao_mock)

    conclude_spy = Mock(side_effect=instance.conclude)
    instance.conclude = conclude_spy

    assert instance.amount_used == 0

    # Act
    instance.iterate_loop()
    assert instance.amount_used == 1

    instance.iterate_loop()
    instance.iterate_loop()
    assert instance.amount_used == 3

    # Assert
    add_ten_mock.assert_not_called()
    deduct_duration_mock.assert_not_called()

    # Act - Pretend the container called .stop()
    instance.conclude()

    conclude_spy.assert_called_once()
    deduct_duration_mock.assert_called_once_with(keep_alive_pulse_delay - 3, session)



def test_multiple_whole_loops():
    dao_mock = Mock()
    add_ten_mock = Mock()
    deduct_duration_mock = Mock()
    dao_mock.deduct_duration = deduct_duration_mock
    dao_mock.add_ten_sec_to_end_time = add_ten_mock
    session = ProgramSession()
    

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
    assert add_ten_mock.call_count == 2
    assert instance.amount_used == total % keep_alive_pulse_delay  # 3

    # Act again
    instance.conclude()
    remainder = instance.calculate_remaining_window(and_then_some)

    assert 10 - and_then_some == remainder, "Setup conditions not met in test"
    # Assert
    deduct_duration_mock.assert_called_with(remainder, session)  


def test_window_usage_calculation():
    dao_mock = Mock()
    deduct_duration_mock = Mock()
    dao_mock.deduct_duration = deduct_duration_mock
    session = ProgramSession()

    instance = KeepAliveEngine(session, dao_mock)

    full_window = keep_alive_pulse_delay
    used_amt = 3
    amount_2 = 9
    amount_5 = 5
    amount_4 = 4

    remainder = instance.calculate_remaining_window(used_amt)
    assert remainder == full_window - used_amt

    remainder = instance.calculate_remaining_window(amount_2)
    assert remainder == full_window - amount_2

    remainder = instance.calculate_remaining_window(amount_5)
    assert remainder == full_window - amount_5

    remainder = instance.calculate_remaining_window(amount_4)
    assert remainder == full_window - amount_4


def test_conclude_calls_deduct_duration():
    dao_mock = Mock()
    deduct_duration_mock = Mock()
    dao_mock.deduct_duration = deduct_duration_mock
    session = ProgramSession()

    instance = KeepAliveEngine(session, dao_mock)
    instance.iterate_loop()
    assert instance.amount_used == 1

    instance.iterate_loop()
    instance.iterate_loop()
    assert instance.amount_used == 3

    # Act
    instance.conclude()

    assert dao_mock.deduct_duration.call_count == 1
    
def test_window_isnt_used_at_all():
    dao_mock = Mock()
    deduct_duration_mock = Mock()
    dao_mock.deduct_duration = deduct_duration_mock
    session = ProgramSession()

    instance = KeepAliveEngine(session, dao_mock)

    instance.conclude()

    deducted_window_len = window_push_length
    
    deduct_duration_mock.assert_called_once_with(deducted_window_len, session)

    final_deduction = deduct_duration_mock.call_args_list[0][0][0]
    assert final_deduction == 10

def test_used_amount_resets_after_full_window():
    dao_mock = Mock()
    session = ProgramSession()

    instance = KeepAliveEngine(session, dao_mock)

    #  Loop ten times
    assert instance.amount_used == 0
    instance.iterate_loop()
    assert instance.amount_used == 1
    instance.iterate_loop()
    assert instance.amount_used == 2
    
    instance.iterate_loop()
    instance.iterate_loop()
    instance.iterate_loop()
    instance.iterate_loop()
    instance.iterate_loop()
    instance.iterate_loop()
    instance.iterate_loop()  # 9
    assert instance.amount_used == 9

    instance.iterate_loop()
    assert instance.amount_used == 0

def test_full_window_is_used():
    dao_mock = Mock()
    deduct_duration_mock = Mock()
    dao_mock.deduct_duration = deduct_duration_mock
    session = ProgramSession()

    instance = KeepAliveEngine(session, dao_mock)

    calculate_remaining_window_spy = Mock(side_effect=instance.calculate_remaining_window)
    instance.calculate_remaining_window = calculate_remaining_window_spy

    internal_deduct_spy = Mock(side_effect=instance._deduct_remainder)
    instance._deduct_remainder = internal_deduct_spy

    #  Loop ten times
    assert window_push_length == 10
    for i in range(0, 6):
        instance.iterate_loop()

    assert instance.amount_used == 6
    instance.conclude()


    internal_deduct_spy.assert_called_once_with(6)
    calculate_remaining_window_spy.assert_called_once_with(6)

    assert deduct_duration_mock.call_args_list[0][0][0] == 4


