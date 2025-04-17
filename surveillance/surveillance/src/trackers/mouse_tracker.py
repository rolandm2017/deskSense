# src/trackers/mouse_tracker.py

from typing import List, TypedDict

from surveillance.src.util.keyboard_aggregator import EventAggregator, InProgressAggregation


# from surveillance.src.object.enums import MouseEvent
from surveillance.src.object.classes import  MouseAggregate, MouseEvent
from surveillance.src.util.console_logger import ConsoleLogger
from surveillance.src.facade.mouse_facade import MouseFacadeCore


class MouseTrackerCore:
    def __init__(self,  mouse_api_facade, event_handlers):
        self.mouse_facade: MouseFacadeCore = mouse_api_facade
        self.event_handlers = event_handlers

        self.aggregator = EventAggregator(
            timeout_ms=1000, aggregate_class=MouseAggregate)
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
                else:
                    # Otherwise, the end of the mouse move might be so great, 
                    # that the end of the event starts a new aggregate
                    self.aggregator.extend_until(event["end"])
                # self.aggregator.add_event(event["end"])
                # if finalized_aggregate:

                #     self.conclude_aggregation(finalized_aggregate)

    def conclude_aggregation(self, finalized_agg):
        session = self.aggregator.package_mouse_events_for_db(
            finalized_agg)
        self.apply_handlers(session)

    def reset(self):
        self.movement_start_time = None

    def apply_handlers(self, content: MouseAggregate | InProgressAggregation):
        # self.logger.log_green("[info] " + str(content))
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
