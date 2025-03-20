# src/trackers/mouse_tracker.py

from typing import List, TypedDict

from ..util.keyboard_aggregator import EventAggregator, InProgressAggregation

from ..util.clock import SystemClock
from ..util.detect_os import OperatingSystemInfo
from ..util.threaded_tracker import ThreadedTracker
# from ..object.enums import MouseEvent
from ..object.classes import KeyboardAggregate, MouseAggregate, MouseCoords, MouseMoveWindow, MouseEvent
from ..util.console_logger import ConsoleLogger
from ..facade.mouse_facade import MouseFacadeCore


class MouseTrackerCore:
    def __init__(self, user_facing_clock, mouse_api_facade, event_handlers, end_program_routine=None):
        self.user_facing_clock = user_facing_clock
        self.mouse_facade: MouseFacadeCore = mouse_api_facade
        self.event_handlers = event_handlers

        self.event_handlers = event_handlers

        self.end_program_func = end_program_routine

        self.aggregator = EventAggregator(
            user_facing_clock, timeout_ms=1000, aggregate_class=MouseAggregate)
        self.logger = ConsoleLogger()

    def run_tracking_loop(self):
        # latest_result: MouseEvent | None = self.mouse_facade.read_event()
        available: List[MouseEvent] = self.mouse_facade.get_all_events()
        # TODO: Handle the fact that the MouseEvents are, are start_time, end_time whereas
        # keyboard events are just, timestamp.
        for event in available:
            if event:
                # NOTE: KISS:
                # If the start_time is from the end of an aggregate,
                # start a new one, and *just assume* that it's OK.
                # Worst case scenario, a new event comes in, it's after that new window has closed,
                # and a third one starts.
                # The aggregator is responding to when the now() runs, NOT when the event actually happened
                finalized_aggregate = self.aggregator.add_event(event["start"])
                if finalized_aggregate:
                    self.conclude_aggregation(finalized_aggregate)
                # it also belongs in the arr
                self.aggregator.add_event(event["end"])

    def conclude_aggregation(self, finalized_agg):
        session = self.aggregator.package_mouse_events_for_db(
            finalized_agg)
        self.apply_handlers(session)

    def reset(self):
        self.movement_start_time = None

    def apply_handlers(self, content: MouseAggregate | InProgressAggregation):
        self.logger.log_green("[info] " + str(content))
        if isinstance(self.event_handlers, list):
            for handler in self.event_handlers:
                handler(content)  # emit an event
        else:
            self.event_handlers(content)  # is a single func

    def stop(self):
        print("Stopping program")
        final_aggregate = self.aggregator.force_complete()
        if final_aggregate:
            self.apply_handlers(final_aggregate)
        self.is_running = False
