# keyboard_tracker.py
import time

from ..util.end_program_routine import end_program_readout, pretend_report_event
from ..object.classes import KeyboardAggregate
from ..util.clock import SystemClock
from ..util.threaded_tracker import ThreadedTracker
from ..util.keyboard_aggregator import EventAggregator, InProgressAggregation
from ..util.console_logger import ConsoleLogger
from ..facade.keyboard_facade import KeyboardApiFacadeCore

average_char_per_word = 5
wpm = 90
char_per_min = 540  # 5 char per word * 90 word per min -> 540 char per min
char_per_sec = 9  # 540 char / 60 sec -> 9 char per sec
required_delay_per_char = 0.08  # 1 sec / 9 char -> 0.111 sec per char

DELAY_TO_AVOID_CPU_HOGGING = required_delay_per_char


class KeyboardTrackerCore:
    def __init__(self, system_clock, keyboard_api_facade, event_handlers, end_program_routine=None):
        self.system_clock = system_clock
        self.keyboard_facade: KeyboardApiFacadeCore = keyboard_api_facade
        self.event_handlers = event_handlers

        self.end_program_func = end_program_routine

        self.events = []
        self.console_logger = ConsoleLogger()
        self.recent_count = 0
        self.time_of_last_terminal_out = system_clock.now()
        self.time_of_last_aggregator_update = None

        # one sec of no typing => close session
        self.aggregator = EventAggregator(system_clock, timeout_ms=1000)

    def run_tracking_loop(self):
        event = self.keyboard_facade.read_event()
        if self.keyboard_facade.is_ctrl_c(event):
            print("### KEYBOARD TRACKER: Detected Ctrl+C ###")
            self.keyboard_facade.trigger_ctrl_c()  # stop program
            return
        if self.keyboard_facade.event_type_is_key_down(event):
            self.recent_count += 1  # per keystroke
            current_time = self.system_clock.now()
            self.time_of_last_aggregator_update = current_time
            # TODO: Add an "autofinish" time, at which point apply_handlers() is called
            finalized_aggregate = self.aggregator.add_event(
                current_time.timestamp())

            if finalized_aggregate is not None:
                session = self.aggregator.package_aggregate_for_db(
                    finalized_aggregate)
                self.apply_handlers(session)
            if self._is_ready_to_log_to_console(current_time):
                # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                # @@@@ Never log the actual key pressed @@@@
                # self.console_logger.log_key_presses(self.recent_count)
                self.recent_count = 0
                self.update_time(current_time)

    def update_time(self, new_time):  # Method exists to enhance testability
        self.time_of_last_terminal_out = new_time

    def apply_handlers(self, content: KeyboardAggregate | InProgressAggregation):
        # length_of_session = content.end_time - content.start_time
        if isinstance(self.event_handlers, list):
            for handler in self.event_handlers:
                handler(content)  # emit an event
        else:
            self.event_handlers(content)  # is a single func

    def _is_ready_to_log_to_console(self, current_time):
        # log key presses every 3 sec
        return self.system_clock.has_elapsed_since(current_time, self.time_of_last_terminal_out, 3)

    def stop(self):
        print("Stopping program")
        final_aggregate = self.aggregator.force_complete()
        if final_aggregate:
            self.apply_handlers(final_aggregate)
        if self.end_program_func:
            report = self.generate_keyboard_report()
            self.end_program_func(report)
        self.is_running = False

    def generate_keyboard_report(self):
        return {"total_inputs": len(self.events)}


if __name__ == "__main__":
    api_facade = KeyboardApiFacadeCore()
    clock = SystemClock()
    # instance = KeyboardTracker(clock, api_facade, [end_program_readout, pretend_report_event])
    # uncomment other line to do way too much logging - plus it keylogs
    instance = KeyboardTrackerCore(clock, api_facade, [pretend_report_event])

    try:
        thread_handler = ThreadedTracker(instance)
        thread_handler.start()
        # Add a way to keep the main thread alive
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        instance.stop()
        # Give the thread time to clean up
        time.sleep(0.5)
