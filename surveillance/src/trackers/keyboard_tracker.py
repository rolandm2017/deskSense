# keyboard_tracker.py
# Old way
import time

from datetime import datetime

from ..util.end_program_routine import end_program_readout, pretend_report_event
from ..object.classes import KeyboardAggregate
from ..util.clock import SystemClock
from ..util.threaded_tracker import ThreadedTracker
from ..util.keyboard_aggregator import EventAggregator, InProgressAggregation
from ..util.console_logger import ConsoleLogger
from ..facade.keyboard_facade import KeyboardFacadeCore


class KeyboardTrackerCore:
    def __init__(self, user_facing_clock, keyboard_api_facade, event_handlers):
        self.user_facing_clock = user_facing_clock
        self.keyboard_facade: KeyboardFacadeCore = keyboard_api_facade
        self.event_handlers = event_handlers

        # self.recent_count = 0
        self.time_of_last_terminal_out = user_facing_clock.now()

        # one sec of no typing => close session
        self.aggregator = EventAggregator(user_facing_clock, timeout_ms=1000)
        self.logger = ConsoleLogger()

    def run_tracking_loop(self):
        # event = self.keyboard_facade.read_event()
        available = self.keyboard_facade.get_all_events()
        for event in available:
            if event:
                # FIXME: Cannot rely on the datetime.now() because, then,
                # The aggregator is responding to when the now() runs, NOT when the event actually happened
                # current_time = self.user_facing_clock.now()
                # NOTE: The event IS a timestamp!
                finalized_aggregate = self.aggregator.add_event(event)
                if finalized_aggregate:
                    session = self.aggregator.package_keyboard_events_for_db(
                        finalized_aggregate)
                    self.apply_handlers(session)

    def apply_handlers(self, content: KeyboardAggregate | InProgressAggregation):
        # length_of_session = content.end_time - content.start_time
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
