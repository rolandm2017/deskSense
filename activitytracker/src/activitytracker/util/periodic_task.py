import asyncio

from activitytracker.db.dao.direct.system_status_dao import SystemStatusDao


class AsyncPeriodicTask:
    """
    Used to run a task such as polling periodically
    """

    def __init__(self, dao: SystemStatusDao, interval_in_sec=5, sleep_func=asyncio.sleep):
        self.dao: SystemStatusDao = dao
        self.interval = interval_in_sec
        # Inject asyncio.sleep to be testable
        self.sleep_func = sleep_func
        self.current_task = None

        self.running = False

    async def _loop(self):
        while self.running:
            self.dao.run_polling_loop()
            await self.sleep_func(self.interval)

    def start(self):
        print("[info] start polling")
        self.running = True
        self.current_task = asyncio.create_task(self._loop())

    def stop(self):
        self.running = False
        if self.current_task:
            self.current_task.cancel()
