import threading


class SyncPeriodicTask:
    """
    Synchronous version of periodic task that works using threads
    """

    def __init__(self, periodic_task, interval_in_sec: int | float = 10):
        self.periodic_task = periodic_task
        self.interval = interval_in_sec
        self.thread = None
        self.stop_event = threading.Event()
        self.is_running = False
        self.DEBUG = False

    def _loop(self):
        loop_count = 0
        # stop_event.wait(n) uses a thread equivalent of time.sleep(n)
        while not self.stop_event.wait(self.interval):
            if self.DEBUG:
                print(f"[polling] running polling loop {self.interval} {loop_count}")
            try:
                self.periodic_task()
            except Exception as e:
                print(f"ERROR in sync task polling loop: {e}")
            loop_count += 1

    def start(self):
        if self.is_running:
            return
        print("[info] start polling")
        self.is_running = True
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        if not self.is_running:
            return
        self.is_running = False
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
