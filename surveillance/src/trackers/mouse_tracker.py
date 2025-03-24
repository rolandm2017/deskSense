# src/trackers/mouse_tracker.py

from typing import List, TypedDict


from ..util.event_aggregator import EventAggregator, InProgressAggregation


# from ..object.enums import MouseEvent
from ..object.classes import KeyboardAggregate, MouseAggregate,  MouseEvent
from ..util.console_logger import ConsoleLogger
from ..facade.mouse_facade import MouseFacadeCore


class MouseTrackerCore:
    def __init__(self,  mouse_api_facade, event_handlers):
        self.mouse_facade: MouseFacadeCore = mouse_api_facade
        self.event_handlers = event_handlers

        self.aggregator = EventAggregator(
            timeout_ms=1000, aggregate_class=MouseAggregate)
        self.logger = ConsoleLogger()

    def run_tracking_loop(self):
        available: List[MouseEvent] = self.mouse_facade.get_all_events()
        # TODO: Handle the fact that the MouseEvents are, are start_time, end_time whereas
        # keyboard events are just, timestamp.
        for event in available:
            if event:
                # FIXME: I smell a bug here. The start of an event can end an aggregate, and then,
                # the end of the event, < 50ms later, starts a new one?
                # It should be, "if the start would end the aggregate, add the end on too, and then clear the aggregator"
                # Or maybe that's e xactly what happens? the start time is outside of the window, so the old window
                # is returned, and then the start & end are the new start of a new one.
                finalized_aggregate = self.aggregator.add_event(event["start"])
                print(finalized_aggregate, "41ru")
                if finalized_aggregate:
                    print(finalized_aggregate, '40ru')
                    self.conclude_aggregation(finalized_aggregate)
                else:
                    # If the start time was inside of the aggregator timeout, then
                    # the end time also belongs in the arr
                    self.aggregator.add_event(event["end"])

    def conclude_aggregation(self, finalized_agg):
        print("Applying handlers!")
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
