import asyncio

from activitytracker.db.dao.direct.system_status_dao import SystemStatusDao


class AsyncPeriodicTask:
    """
    Used to run a task such as polling periodically
    """

    def __init__(self, dao, interval_in_sec: int | float = 10, sleep_func=asyncio.sleep):
        self.dao = dao
        self.interval = interval_in_sec
        # Inject asyncio.sleep to be testable
        self.sleep_func = sleep_func
        self.current_task = None
        self.loop_count = 0
        self.is_running = False
        self.DEBUG = False

    async def _loop(self):
        while self.is_running:
            if self.DEBUG:
                print("[polling shell] running polling loop", self.interval, self.loop_count)
            try:
                self.dao.run_polling_loop()
            except Exception as e:
                print(f"ERROR in polling loop: {e}")
            self.loop_count += 1
            await self.sleep_func(self.interval)

    def start(self):
        print("[info] start polling")
        self.is_running = True
        self.current_task = asyncio.create_task(self._loop())

    def stop(self):
        self.is_running = False
        if self.current_task:
            self.current_task.cancel()
