# test_keyboard_tracker.py
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from surveillance.src.trackers.keyboard_tracker import KeyboardTrackerCore
from surveillance.src.util.threaded_tracker import ThreadedTracker
from surveillance.src.object.classes import KeyboardAggregate
from ..mocks.mock_clock import MockClock


class MockKeyboardFacade:
    def __init__(self):
        self.current_event = None
        self.ctrl_c_triggered = False
        self.available = []

    def read_event(self):
        return self.current_event

    def set_event(self, event):
        self.available.append(event)

    def event_type_is_key_down(self, event):
        return event is not None

    def is_ctrl_c(self, event):
        return event == 'ctrl+c'

    def trigger_ctrl_c(self):
        self.ctrl_c_triggered = True

    def get_all_events(self):
        temp = self.available
        self.available = []
        return temp


@pytest.fixture
def mock_clock():
    times = [
        datetime(2025, 1, 1, 12, 0, 0),
        datetime(2025, 1, 1, 12, 0, 1),
        datetime(2025, 1, 1, 12, 0, 1),
        datetime(2025, 1, 1, 12, 0, 1),
        datetime(2025, 1, 1, 12, 0, 1),
        datetime(2025, 1, 1, 12, 0, 2),
        datetime(2025, 1, 1, 12, 0, 3),
        datetime(2025, 1, 1, 12, 0, 8),
        datetime(2025, 1, 1, 12, 0, 9),
        datetime(2025, 1, 1, 12, 0, 12),
        datetime(2025, 1, 1, 12, 0, 15),
        datetime(2025, 1, 1, 12, 0, 16),
        datetime(2025, 1, 1, 12, 0, 17),
        datetime(2025, 1, 1, 12, 0, 19),
        datetime(2025, 1, 1, 12, 0, 21),
        datetime(2025, 1, 1, 12, 0, 22),
        datetime(2025, 1, 1, 12, 0, 22),
        datetime(2025, 1, 1, 12, 0, 23),
        datetime(2025, 1, 1, 12, 0, 23),
        datetime(2025, 1, 1, 12, 0, 23),
        datetime(2025, 1, 1, 12, 0, 23),
        datetime(2025, 1, 1, 12, 0, 23),
        datetime(2025, 1, 1, 12, 0, 23),
        datetime(2025, 1, 1, 12, 0, 23)
    ]
    return MockClock(times)


@pytest.fixture
def mock_keyboard_facade():
    return MockKeyboardFacade()


@pytest.fixture
def event_collector():
    handler_events = []

    def event_handler(event):
        handler_events.append(event)

    return handler_events, event_handler


@pytest.fixture
def tracker_and_events(mock_keyboard_facade, event_collector):
    events, handler = event_collector
    tracker = KeyboardTrackerCore(mock_keyboard_facade, handler)
    return tracker, events


def test_tracker_initialization(tracker_and_events):
    """Test that KeyboardTracker initializes correctly."""
    tracker = tracker_and_events[0]
    assert tracker.aggregator.current_aggregation is None


def test_key_press_tracking(tracker_and_events, mock_keyboard_facade):
    """Test that key presses are tracked correctly."""
    tracker = tracker_and_events[0]
    handler_events = tracker_and_events[1]

    now = datetime.now() - timedelta(hours=1)
    t1 = now - timedelta(seconds=10)
    t1_t = t1.timestamp()
    t2 = t1 + timedelta(milliseconds=2)
    t2_t = t2.timestamp()

    t3 = t2 + timedelta(milliseconds=1005)
    t3a = t3 + timedelta(milliseconds=2)
    t3b = t3a + timedelta(milliseconds=3)

    t3_t = t3.timestamp()
    t3a_t = t3a.timestamp()
    t3b_t = t3b.timestamp()

    t4 = t3b + timedelta(milliseconds=4)
    t4_t = t4.timestamp()
    t5 = t4 + timedelta(milliseconds=1006)
    t5_t = t5.timestamp()
    t6 = t5 + timedelta(milliseconds=1)
    t6_t = t6.timestamp()
    t7 = t6 + timedelta(milliseconds=2)
    t7_t = t7.timestamp()
    t8_closer = t7 + timedelta(milliseconds=1033)
    t8_t_closer = t8_closer.timestamp()
    t9 = t8_closer + timedelta(milliseconds=4)
    t9_t = t9.timestamp()

    with patch.object(tracker.aggregator, 'add_event', wraps=tracker.aggregator.add_event) as mock_add_event:
        # ### Test a setup condition
        assert mock_add_event.call_count == 0

        # ### Run the real test
        print("INPUTS: ", t1_t, t2_t)
        mock_keyboard_facade.set_event(t1_t)
        tracker.run_tracking_loop()

        mock_keyboard_facade.set_event(t2_t)
        tracker.run_tracking_loop()

        assert mock_add_event.call_count == 2
        # You can also check the specific calls if needed:
        call_args = [call[0][0] for call in mock_add_event.call_args_list]
        assert len(call_args) == 2

        # Simulate a key press
        mock_keyboard_facade.set_event(t3_t)
        mock_keyboard_facade.set_event(t3a_t)
        mock_keyboard_facade.set_event(t3b_t)

        tracker.run_tracking_loop()

        assert len(tracker.aggregator.current_aggregation.events) == 3
        # Because the window closed due to t3's 1005 ms timedelta
        assert len(handler_events) == 1

        some_event_past_the_aggregator_timeout = t4_t
        # Test the test:
        assert t4 > t1 + timedelta(milliseconds=100)
        mock_keyboard_facade.set_event(some_event_past_the_aggregator_timeout)
        tracker.run_tracking_loop()

        assert len(handler_events) == 1

        # t3, t3a, t3b, t4:
        assert len(tracker.aggregator.current_aggregation.events) == 4

        deliverable_for_db = handler_events[0]   # Note "events[0]"
        assert isinstance(deliverable_for_db, KeyboardAggregate)
        assert deliverable_for_db.start_time is not None
        assert deliverable_for_db.end_time is not None
        # assert all(isinstance(some_time, datetime) for some_time in my_times)

        #
        # Now, moving the clock forward two seconds (not one, but two)
        # will close the session.
        #

        mock_keyboard_facade.set_event(t5_t)
        tracker.run_tracking_loop()
        assert len(tracker.aggregator.current_aggregation.events) == 1
        assert len(
            handler_events) == 2, "The aggregator timeout window wasn't closed 2x"

        mock_keyboard_facade.set_event(t6_t)
        tracker.run_tracking_loop()
        mock_keyboard_facade.set_event(t7_t)
        tracker.run_tracking_loop()

        events = tracker.aggregator.current_aggregation.events
        assert t5_t in events
        assert t6_t in events
        assert t7_t in events
        assert len(tracker.aggregator.current_aggregation.events) == 3

        mock_keyboard_facade.set_event(t8_t_closer)
        tracker.run_tracking_loop()

        events = tracker.aggregator.current_aggregation.events
        assert t5_t not in events
        assert t6_t not in events
        assert t7_t not in events

        assert t8_t_closer in events
        assert len(tracker.aggregator.current_aggregation.events) == 1
        assert len(
            handler_events) == 3, "The aggregator timeout window wasn't closed 3x"


# def move_time_fwd_one_ms(d):
#     return d + timedelta(milliseconds=1)


# def test_multiple_key_presses(tracker_and_events, mock_keyboard_facade):
#     """Test tracking of multiple key presses."""

#     now = datetime.now()
#     t1 = now - timedelta(seconds=10)
#     t2 = t1 + timedelta(milliseconds=100)
#     t3 = t2 + timedelta(milliseconds=101)
#     t4 = t3 + timedelta(milliseconds=50)
#     t5 = t4 + timedelta(milliseconds=55)
#     t6 = t5 + timedelta(milliseconds=1001)
#     t7 = t6 + timedelta(milliseconds=22)
#     t8 = t7 + timedelta(milliseconds=23)
#     t9 = t8 + timedelta(milliseconds=24)
#     t10 = move_time_fwd_one_ms(t9)
#     t11 = move_time_fwd_one_ms(t10)
#     t12 = move_time_fwd_one_ms(t11)
#     t13 = move_time_fwd_one_ms(t12)
#     times = [t1, t2, t3, t4, t5, t6, t7, t8,
#              t9, t10, t11, t12, t13, t13]
    
#     timestamps = []

#     sys_clock = MockClock(times)
#     handler_events = []

#     def event_handler(event):
#         handler_events.append(event)

#     tracker_core = KeyboardTrackerCore(mock_keyboard_facade, event_handler)

#     # Simulate multiple key presses
#     # first five occur within same timespan in Clock
#     keys = ['a', 'b', 'c', 'd', 'e']
#     for key in keys:
#         mock_keyboard_facade.set_event(key)
#         tracker_core.run_tracking_loop()

#     mock_keyboard_facade.set_event("f")  # Occurs after the window closes
#     tracker_core.run_tracking_loop()  # Should close the aggregator loop

#     assert isinstance(handler_events[0], KeyboardAggregate)
#     assert handler_events[0].start_time is not None
#     assert handler_events[0].end_time is not None
#     assert len(handler_events) == 1


# def test_multiple_handlers_are_called(tracker_and_events, mock_keyboard_facade):
#     """Test that when multiple handlers are provided, they are all called."""
#     tracker = tracker_and_events[0]
#     handler1_calls = []
#     handler2_calls = []

#     def handler1(event):
#         handler1_calls.append(event)

#     def handler2(event):
#         handler2_calls.append(event)

#     tracker.event_handlers = [handler1, handler2]

#     mock_keyboard_facade.set_event('x')
#     tracker.run_tracking_loop()

#     assert len(handler1_calls) == len(handler2_calls) == 0

#     mock_keyboard_facade.set_event('y')
#     tracker.run_tracking_loop()

#     assert len(handler1_calls) == 1
#     assert len(handler2_calls) == 1

#     assert handler1_calls[0] == handler2_calls[0]



