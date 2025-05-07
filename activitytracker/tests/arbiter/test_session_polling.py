import pytest
from unittest.mock import AsyncMock, Mock, patch

import asyncio

import time

from activitytracker.arbiter.session_polling import (
    KeepAliveEngine,
    ThreadedEngineContainer,
)
from activitytracker.config.definitions import (
    keep_alive_cycle_length,
    window_push_length,
)
from activitytracker.object.classes import ProgramSession


class MockDaoConn:
    """
    Mocking ActivityRecorder
    """

    def __init__(self):
        pass

    def add_ten_sec_to_end_time(self):
        pass

    def add_partial_window(self):
        pass


# Custom sleep function that does nothing


def fast_sleep(_):
    pass


def test_window_addition_math():
    """ """
    dao_mock = Mock()

    add_ten_mock = Mock()
    dao_mock.add_ten_sec_to_end_time = add_ten_mock

    add_partial_window_spy = Mock()
    dao_mock.add_partial_window = add_partial_window_spy

    session = ProgramSession()
    # --
    # -- instance 1
    # --

    # The program opens a new window. Ten sec remain
    instance = KeepAliveEngine(session, dao_mock)

    # Loops twice, using 2 sec
    partial_cycle_loops = 2

    instance.iterate_loop()
    instance.iterate_loop()

    # The Engine concludes:
    instance.conclude()

    # So add_partial_window was called with the remainder:
    add_partial_window_spy.assert_called_once_with(partial_cycle_loops, session)

    add_partial_window_spy.reset_mock()

    # --
    # -- instance 2
    # --
    # The program opens a new window. Ten sec remain
    used_amount = 0
    instance = KeepAliveEngine(session, dao_mock)

    # Loops 0 times before concluding.
    instance.conclude()

    # Used time is added to duration
    add_ten_mock.assert_not_called()
    add_partial_window_spy.assert_called_once_with(used_amount, session)

    add_partial_window_spy.reset_mock()

    # --
    # -- instance 3
    # --
    # The program opens a new window. Ten sec remain
    used_amount = 0
    instance = KeepAliveEngine(session, dao_mock)

    used_amount = 7
    one_full_cycyle = window_push_length  # 10

    total_loops = used_amount + one_full_cycyle

    for i in range(0, total_loops):
        instance.iterate_loop()

    instance.conclude()

    add_partial_window_spy.assert_called_once()
    assert add_partial_window_spy.call_args_list[0][0][0] == used_amount


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
    assert instance.max_interval == keep_alive_cycle_length

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
    add_duration_mock = Mock()
    dao_mock.add_ten_sec_to_end_time = add_ten_mock
    dao_mock.add_duration = add_duration_mock
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
    # max_int is 10, so range(x, 10) takes us to 9
    end_of_9th_loop = max_interval
    for i in range(start_of_4th_loop, end_of_9th_loop):
        instance.iterate_loop()
        assert instance.amount_used == i

    instance.iterate_loop()

    assert instance.amount_used == 0  # The counter reset

    pulse_add_ten_spy.assert_called_once()
    add_duration_mock.assert_not_called()

    add_ten_mock.assert_called_once_with(session)


def test_running_for_three_sec():
    dao_mock = Mock()
    add_ten_mock = Mock()
    dao_mock.add_ten_sec_to_end_time = add_ten_mock

    add_partial_window_mock = Mock()
    dao_mock.add_partial_window = add_partial_window_mock

    session = ProgramSession()

    instance = KeepAliveEngine(session, dao_mock)

    conclude_spy = Mock(side_effect=instance.conclude)
    instance.conclude = conclude_spy

    assert instance.amount_used == 0

    # Act
    instance.iterate_loop()
    assert instance.amount_used == 1

    instance.iterate_loop()
    assert instance.amount_used == 2
    instance.iterate_loop()
    final_loop_amt = 3
    assert instance.amount_used == final_loop_amt

    # Assert
    add_ten_mock.assert_not_called()
    add_partial_window_mock.assert_not_called()

    # Act - Pretend the container called .stop()
    instance.conclude()

    conclude_spy.assert_called_once()
    add_partial_window_mock.assert_called_once_with(final_loop_amt, session)


def test_multiple_whole_loops():
    dao_mock = Mock()
    add_ten_mock = Mock()
    add_partial_window_mock = Mock()
    dao_mock.add_partial_window = add_partial_window_mock
    dao_mock.add_ten_sec_to_end_time = add_ten_mock
    session = ProgramSession()

    instance = KeepAliveEngine(session, dao_mock)

    conclude_spy = Mock(side_effect=instance.conclude)
    instance.conclude = conclude_spy

    two_whole_loops = 20
    partial_incomplete_cycle = 3
    total = two_whole_loops + partial_incomplete_cycle

    for i in range(total):
        instance.iterate_loop()

    # Assert
    conclude_spy.assert_not_called
    assert add_ten_mock.call_count == 2
    assert instance.amount_used == total % keep_alive_cycle_length  # 3

    # Act again
    instance.conclude()

    # Assert
    add_partial_window_mock.assert_called_with(partial_incomplete_cycle, session)


def test_conclude_calls_add_partial_window():
    dao_mock = Mock()
    add_partial_window_mock = Mock()
    dao_mock.add_partial_window = add_partial_window_mock
    session = ProgramSession()

    instance = KeepAliveEngine(session, dao_mock)
    instance.iterate_loop()
    assert instance.amount_used == 1

    instance.iterate_loop()
    instance.iterate_loop()
    assert instance.amount_used == 3

    # Act
    instance.conclude()

    assert dao_mock.add_partial_window.call_count == 1


def test_window_isnt_used_at_all():
    dao_mock = Mock()

    add_ten_sec_to_end_time_mock = Mock()
    dao_mock.add_ten_sec_to_end_time = add_ten_sec_to_end_time_mock

    add_partial_window_mock = Mock()
    dao_mock.add_partial_window = add_partial_window_mock

    session = ProgramSession()

    instance = KeepAliveEngine(session, dao_mock)

    assert instance.amount_used == 0
    instance.conclude()

    add_ten_sec_to_end_time_mock.assert_not_called()
    add_partial_window_mock.assert_called_once_with(0, session)

    final_addition = add_partial_window_mock.call_args_list[0][0][0]
    assert final_addition == 0


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

    add_ten_sec_to_end_time_mock = Mock()
    dao_mock.add_ten_sec_to_end_time = add_ten_sec_to_end_time_mock

    add_partial_window_mock = Mock()
    dao_mock.add_partial_window = add_partial_window_mock

    session = ProgramSession()

    instance = KeepAliveEngine(session, dao_mock)

    internal_add_spy = Mock(side_effect=instance._add_partial_window)
    instance._add_partial_window = internal_add_spy

    #  Loop ten times
    assert window_push_length == 10

    partial_cycle = 6
    for i in range(0, partial_cycle):
        instance.iterate_loop()

    assert instance.amount_used == partial_cycle
    instance.conclude()

    internal_add_spy.assert_called_once_with(partial_cycle)


def test_numerous_full_cycles():
    dao_mock = Mock()

    add_ten_sec_to_end_time_mock = Mock()
    dao_mock.add_ten_sec_to_end_time = add_ten_sec_to_end_time_mock

    add_partial_window_mock = Mock()
    dao_mock.add_partial_window = add_partial_window_mock
    session = ProgramSession()

    iteration_count = 63

    instance = KeepAliveEngine(session, dao_mock)

    for _ in range(0, iteration_count):
        instance.iterate_loop()

    instance.conclude()

    assert add_ten_sec_to_end_time_mock.call_count == 6  # 60 / 10

    time_arg = add_partial_window_mock.call_args_list[0][0][0]
    assert time_arg == 3


class TestThreadedEngineContainer:
    @pytest.mark.asyncio
    async def test_engine_container(self):
        iterate_loop_mock = Mock()
        conclude_mock = Mock()

        dao_mock = Mock()
        session = ProgramSession()

        engine = KeepAliveEngine(session, dao_mock)

        engine.conclude = conclude_mock
        engine.iterate_loop = iterate_loop_mock

        quick_test_interval = 0.02
        container = ThreadedEngineContainer(quick_test_interval, time.sleep)

        container.add_first_engine(engine)

        assert container.engine is not None

        container.start()

        sleep_time = 0.25
        await asyncio.sleep(sleep_time)

        assert container.is_running is True

        container.stop()

        assert container.is_running is False

        # Because the thread runs a whole lot of times
        assert iterate_loop_mock.call_count >= int(sleep_time / quick_test_interval)

        conclude_mock.assert_called_once()
