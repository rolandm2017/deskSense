import threading

import traceback


class EventBasedThreadedTracker:
    """
    More sophisticated wrapper that can properly interrupt X11 event loops.

    This class is used instead of ThreadedTracker because
    the ProgramTracker is event-based.
    """

    def __init__(self, event_tracker):
        self.tracker = event_tracker
        self.stop_event = threading.Event()
        self.thread = None
        self.is_running = False

    def start(self):
        if self.is_running:
            return

        self.thread = threading.Thread(
            target=self._run_with_interruption, name="ProgramTrackerThread"
        )
        self.thread.daemon = True
        self.thread.start()
        self.is_running = True

    def _run_with_interruption(self):
        """Run tracker with proper interruption handling."""
        try:
            # Pass the stop_event to the tracker so it can check for interruption
            # if hasattr(self.tracker, "run_forever_interruptible"):
            #     self.tracker.run_forever_interruptible(self.stop_event)
            # else:
            # Fallback to regular run_forever
            self.tracker.run_tracking_loop()
        except KeyboardInterrupt:
            print(
                f"[THREAD {threading.current_thread().name}] Caught Ctrl+C in event thread"
            )
        except Exception as e:
            traceback.print_exc()
            print(f"[THREAD {threading.current_thread().name}] Error in event tracker: {e}")
        finally:
            print(f"[THREAD {threading.current_thread().name}] Event loop ending")
            self.is_running = False

    def stop(self):
        print("Stopping Eventful Threaded Tracker")
        if not self.is_running:
            return

        self.stop_event.set()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)

        self.is_running = False
