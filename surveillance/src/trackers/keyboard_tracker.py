# keyboard_tracker.py
# from datetime import datetime, timedelta
# import asyncio
# import csv
import threading
import time
# from pathlib import Path

from ..util.end_program_routine import end_program_readout, pretend_report_event
# from ..util.interrupt_handler import InterruptHandler
from ..util.clock import Clock
from ..util.threaded_tracker import ThreadedTracker
from ..console_logger import ConsoleLogger
from ..facade.keyboard_facade import KeyboardApiFacadeCore

average_char_per_word = 5
wpm = 90
char_per_min = 540  # 5 char per word * 90 word per min -> 540 char per min
char_per_sec = 9  # 540 char / 60 sec -> 9 char per sec
required_delay_per_char = 0.08  # 1 sec / 9 char -> 0.111 sec per char

DELAY_TO_AVOID_CPU_HOGGING = required_delay_per_char

class KeyboardTrackerCore:
    def __init__(self, clock, keyboard_api_facade, event_handlers, end_program_routine=None):
        self.clock = clock
        self.keyboard_facade: KeyboardApiFacadeCore = keyboard_api_facade
        self.event_handlers = event_handlers

        self.end_program_func = end_program_routine
        
        self.events = []
        # so surveillanceManager can grab the interval data
        self.session_data = []
        self.console_logger = ConsoleLogger()
        self.recent_count = 0
        self.time_of_last_terminal_out = clock.now()

    def run_tracking_loop(self):
        event = self.keyboard_facade.read_event()
        if self.keyboard_facade.is_ctrl_c(event):
            self.keyboard_facade.trigger_ctrl_c()  # stop program
        if self.keyboard_facade.event_type_is_key_down(event):
            current_time = self.clock.now()
            self.apply_handlers(event)
            # TODO: 'If no keystroke within 300 ms, end sesion; report session to db'
            self.recent_count += 1  # per keystroke
            # print("Increasing recent count, 47ru")
            if self._is_ready_to_log_to_console(current_time): 
                # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
                # @@@@ Please never log the actual key pressed @@@@
                self.console_logger.log_key_presses(self.recent_count)
                # print("Resetting recent count, 52ru")
                self.recent_count = 0
                self.update_time(current_time)

    def update_time(self, new_time):  # Method exists to enhance testability
        self.time_of_last_terminal_out = new_time

    def apply_handlers(self, content):
        print("Applying handlers, 58ru")
        if isinstance(self.event_handlers, list):
            for handler in self.event_handlers:
                print("Handler applied, 61ru")
                handler(content)  # emit an event
        else:
            self.event_handlers(content)  # is a single func                

    def _is_ready_to_log_to_console(self, current_time):
        # log key presses every 3 sec
        return self.clock.has_elapsed_since(current_time, self.time_of_last_terminal_out, 3)
        
    def gather_session(self):
        current = self.session_data
        self.session_data = []
        return current

    def stop(self):
        print("Stopping program")
        if self.end_program_func:
            report = self.generate_keyboard_report()
            self.end_program_func(report)
        self.is_running = False

    def generate_keyboard_report(self):
        return {"total_inputs": len(self.events)}



if __name__ == "__main__":
    api_facade = KeyboardApiFacadeCore()
    clock = Clock()
    # instance = KeyboardTracker(clock, api_facade, [end_program_readout, pretend_report_event])
    instance = KeyboardTracker(clock, api_facade, [pretend_report_event])  # uncomment other line to do way too much logging - plus it keylogs
    
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
