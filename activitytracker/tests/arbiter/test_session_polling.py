import pytest
from unittest.mock import AsyncMock, Mock, patch

import asyncio
import threading

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
    instance.conclude_engine()

    # So add_partial_window was called with the remainder:
    call_args = add_partial_window_spy.call_args[0]  # Get positional args
    assert call_args[0] == partial_cycle_loops  # First arg
    assert call_args[1] == session  # Second arg
    # Ignore third arg

    add_partial_window_spy.reset_mock()

    # --
    # -- instance 2
    # --
    # The program opens a new window. Ten sec remain
    used_amount = 0
    instance = KeepAliveEngine(session, dao_mock)

    # Loops 0 times before concluding.
    instance.conclude_engine()

    # Used time is added to duration
    assert add_ten_mock.call_count == 0
    assert add_partial_window_spy.call_count == 1

    call_args = add_partial_window_spy.call_args[0]  # Get positional args
    assert call_args[0] == used_amount  # First arg
    assert call_args[1] == session  # Second arg

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

    instance.conclude_engine()

    add_partial_window_spy.assert_called_once()

    call_args = add_partial_window_spy.call_args[0]  # Get positional args
    assert call_args[0] == used_amount  # First arg
    assert call_args[1] == session  # Second arg


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
    assert engine.amount_used == 0

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

    conclude_spy = Mock(side_effect=instance.conclude_engine)
    instance.conclude_engine = conclude_spy

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
    instance.conclude_engine()

    conclude_spy.assert_called_once()

    call_args = add_partial_window_mock.call_args[0]  # Get positional args
    assert call_args[0] == final_loop_amt  # First arg
    assert call_args[1] == session  # Second arg


def test_multiple_whole_loops():
    dao_mock = Mock()
    add_ten_mock = Mock()
    add_partial_window_mock = Mock()
    dao_mock.add_partial_window = add_partial_window_mock
    dao_mock.add_ten_sec_to_end_time = add_ten_mock
    session = ProgramSession()

    instance = KeepAliveEngine(session, dao_mock)

    conclude_spy = Mock(side_effect=instance.conclude_engine)
    instance.conclude_engine = conclude_spy

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
    instance.conclude_engine()

    # Assert
    call_args = add_partial_window_mock.call_args[0]  # Get positional args
    assert call_args[0] == partial_incomplete_cycle  # First arg
    assert call_args[1] == session  # Second arg


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
    instance.conclude_engine()

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
    instance.conclude_engine()

    add_ten_sec_to_end_time_mock.assert_not_called()

    call_args = add_partial_window_mock.call_args[0]  # Get positional args
    assert call_args[0] == 0  # First arg
    assert call_args[1] == session  # Second arg

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
    instance.conclude_engine()

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

    instance.conclude_engine()

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

        engine.conclude_engine = conclude_mock
        engine.iterate_loop = iterate_loop_mock

        quick_test_interval = 0.02
        container = ThreadedEngineContainer(quick_test_interval, time.sleep)

        assert container.engine is None

        container.add_first_engine(engine)

        assert container.engine is not None  # first engine loaded directly

        container.start()

        await asyncio.sleep(0.04)  # Give time for engine to load

        sleep_time = 0.25
        await asyncio.sleep(sleep_time)

        assert container.is_running is True

        container.stop()

        assert container.is_running is False

        # Because the thread runs a whole lot of times
        assert iterate_loop_mock.call_count >= int(sleep_time / quick_test_interval)

        conclude_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_engine_durations_without_start_stop(self):
        dao_mock = Mock()
        add_ten_sec_to_end_time_mock = Mock()
        dao_mock.add_ten_sec_to_end_time = add_ten_sec_to_end_time_mock
        add_partial_window_mock = Mock()
        dao_mock.add_partial_window = add_partial_window_mock

        session = ProgramSession()

        # FYI a value like 9 may end up cycling a full time
        durations = [63, 30, 5, 6]
        engines = []
        for i in range(len(durations)):
            session = ProgramSession()
            session.process_name = f"rapid_test_{i}"
            engine = KeepAliveEngine(session, dao_mock)
            engine.iterate_loop = Mock(
                wraps=engine.iterate_loop
            )  # Spy but still run real method
            engine.conclude_engine = Mock(wraps=engine.conclude_engine)
            # Utility for debugging:
            engine._hit_max_window = Mock(wraps=engine._hit_max_window)
            engines.append(engine)

        quick_test_interval = 0.02
        container = ThreadedEngineContainer(quick_test_interval, time.sleep)

        add_ten_mock_call_counts = []
        iterate_loop_counts = []
        try:
            # Deal with first engine outside of loop
            container.add_first_engine(engines[0])
            assert container.engine is not None
            container.start()
            assert container.is_running is True

            print("486ru")

            sleep_time = quick_test_interval * durations[0]
            await asyncio.sleep(sleep_time)

            add_ten_mock_call_counts.append(add_ten_sec_to_end_time_mock.call_count)
            iterate_loop_counts.append(engines[i].iterate_loop.call_count)

            for i in range(1, len(durations)):
                # Reset the mock call count for this engine's measurements
                print("adding engine ", i)
                add_ten_sec_to_end_time_mock.reset_mock()

                print("496ru")
                container.replace_engine(engines[i])

                # Give a moment for the replacement to happen
                await asyncio.sleep(0.05)

                sleep_time = quick_test_interval * durations[i]
                await asyncio.sleep(sleep_time)

                add_ten_mock_call_counts.append(add_ten_sec_to_end_time_mock.call_count)
                iterate_loop_counts.append(engines[i].iterate_loop.call_count)
        except Exception as e:
            print(e)
            raise e

        finally:
            print("Stopping container...")
            container.stop()

            # Check REALLY BASIC stuff:

            assert len(iterate_loop_counts) == len(durations)
            assert len(add_ten_mock_call_counts) == len(durations)

            print("Checking conclude_engine calls:")
            for i, engine in enumerate(engines):
                print(
                    f"Engine {i}: conclude_engine called {engine.conclude_engine.call_count} times."
                )
                print(
                    f"Engine {i} hit max window count: {engine._hit_max_window.call_count}"
                )

            iterate_loop_called_nonzero_times = any(x != 0 for x in iterate_loop_counts)
            assert iterate_loop_called_nonzero_times

            for f in iterate_loop_counts:
                print("f:", f)

            add_ten_called_nonzero_times = any(x != 0 for x in add_ten_mock_call_counts)
            assert add_ten_called_nonzero_times

            for k in add_ten_mock_call_counts:
                print(k, "k")

            for i, count in enumerate(add_ten_mock_call_counts):
                # FYI a duration like 8 or 28 may cycle once more than expected
                expected = durations[i] // window_push_length
                print(count, expected, durations[i], "comparison ")
                assert count == expected

            assert container.is_running is False

            # Check that all engines except the last were concluded during replacement
            for i in range(len(engines) - 1):
                engines[i].conclude_engine.assert_called_once()

            # Last engine should be concluded during stop
            engines[-1].conclude_engine.assert_called_once()

            print("Checking add_partial_window calls:")
            print(f"Total add_partial_window calls: {add_partial_window_mock.call_count}")

            # Each engine should have been concluded exactly once
            assert add_partial_window_mock.call_count == len(engines)

            # Cannot check exactly what partial amt was used because
            # the async sleeps run an indeterminate amount of time

    @pytest.mark.asyncio
    async def test_engine_container_replacement_lifecycle(self):
        """Test that engines are properly replaced and concluded in the correct thread"""

        # Setup mocks for multiple engines
        engines = []
        dao_mock = Mock()
        dao_mock.add_ten_sec_to_end_time = Mock()
        dao_mock.add_partial_window = Mock()

        # Create 3 test engines with different sessions
        for i in range(3):
            session = ProgramSession()
            session.process_name = f"test_program_{i}"

            engine = KeepAliveEngine(session, dao_mock)
            engine.iterate_loop = Mock()
            engine.conclude_engine = Mock()
            engines.append(engine)

        quick_test_interval = 0.02
        container = ThreadedEngineContainer(quick_test_interval, time.sleep)

        # Start with first engine
        container.add_first_engine(engines[0])
        container.start()

        try:
            # Let first engine run for a bit
            await asyncio.sleep(0.1)
            first_engine_calls = engines[0].iterate_loop.call_count
            assert first_engine_calls > 0
            assert engines[0].conclude_engine.call_count == 0  # Not concluded yet

            # Replace with second engine
            container.replace_engine(engines[1])
            await asyncio.sleep(0.1)

            # First engine should be concluded, second should be running
            engines[0].conclude_engine.assert_called_once()
            assert engines[1].iterate_loop.call_count > 0
            assert engines[1].conclude_engine.call_count == 0  # Not concluded yet

            # Replace with third engine
            container.replace_engine(engines[2])
            await asyncio.sleep(0.1)

            # Second engine should be concluded, third should be running
            engines[1].conclude_engine.assert_called_once()
            assert engines[2].iterate_loop.call_count > 0
            assert engines[2].conclude_engine.call_count == 0  # Not concluded yet

            # Verify first engine stopped being called after replacement
            first_engine_final_calls = engines[0].iterate_loop.call_count
            assert first_engine_final_calls == first_engine_calls  # No new calls

        finally:
            # Stop container
            container.stop()

            # Final engine should be concluded during stop
            engines[2].conclude_engine.assert_called_once()
            assert container.is_running is False

    @pytest.mark.asyncio
    async def test_engine_container_thread_ownership(self):
        """Test that conclude_engine is called from the KeepAlive thread"""

        dao_mock = Mock()
        dao_mock.add_ten_sec_to_end_time = Mock()
        dao_mock.add_partial_window = Mock()

        session = ProgramSession()
        session.process_name = "test_program"

        # Track which thread called conclude_engine
        conclusion_thread_name = None

        def mock_conclude():
            nonlocal conclusion_thread_name
            conclusion_thread_name = threading.current_thread().name

        engine = KeepAliveEngine(session, dao_mock)
        engine.iterate_loop = Mock()
        engine.conclude_engine = Mock(side_effect=mock_conclude)

        container = ThreadedEngineContainer(0.02, time.sleep)
        container.add_first_engine(engine)
        container.start()

        try:
            await asyncio.sleep(0.05)  # Let it run briefly

            # Create replacement engine
            new_session = ProgramSession()
            new_session.process_name = "replacement_program"
            new_engine = KeepAliveEngine(new_session, dao_mock)
            new_engine.iterate_loop = Mock()
            new_engine.conclude_engine = Mock()

            # Replace engine (this call happens from test thread)
            test_thread_name = threading.current_thread().name
            container.replace_engine(new_engine)

            await asyncio.sleep(0.05)  # Wait for replacement to be processed

            # Verify conclude was called from KeepAlive thread, not test thread
            engine.conclude_engine.assert_called_once()
            assert conclusion_thread_name is not None
            assert conclusion_thread_name.startswith("KeepAlive-")
            assert conclusion_thread_name != test_thread_name

        finally:
            container.stop()

    @pytest.mark.asyncio
    async def test_engine_container_queue_behavior(self):
        """Test that multiple rapid replacements are handled correctly"""

        dao_mock = Mock()
        dao_mock.add_ten_sec_to_end_time = Mock()
        dao_mock.add_partial_window = Mock()

        engines = []
        for i in range(5):
            session = ProgramSession()
            session.process_name = f"rapid_test_{i}"
            engine = KeepAliveEngine(session, dao_mock)
            engine.iterate_loop = Mock()
            engine.conclude_engine = Mock()
            engines.append(engine)

        container = ThreadedEngineContainer(0.01, time.sleep)  # Very fast for this test
        container.add_first_engine(engines[0])
        container.start()

        try:
            # Rapidly queue multiple replacements
            for i in range(1, 5):
                container.replace_engine(engines[i])
                await asyncio.sleep(0.005)  # Very brief pause

            # Wait for all replacements to be processed
            await asyncio.sleep(0.1)

            # All but the last engine should be concluded
            for i in range(4):
                assert engines[i].conclude_engine.call_count == 1

            # Last engine should still be running
            assert engines[4].conclude_engine.call_count == 0
            assert engines[4].iterate_loop.call_count > 0

        finally:
            container.stop()
            # Last engine should be concluded on stop
            engines[4].conclude_engine.assert_called_once()
