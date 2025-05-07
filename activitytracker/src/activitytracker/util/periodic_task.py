import asyncio

from activitytracker.db.dao.direct.system_status_dao import SystemStatusDao


class AsyncPeriodicTask:
    """
    Used to run a task such as polling periodically
    """

    def __init__(self, dao: SystemStatusDao, interval_in_sec=5):
        self.dao: SystemStatusDao = dao
        self.interval = interval_in_sec
        self.current_task = None

        self.running = False

    async def _loop(self):
        while self.running:
            await asyncio.sleep(5)
            self.dao.run_polling_loop()

    async def write_to_db_and_update(self):
        print("Writing to DB...")  # Replace with actual logic

    def start(self):
        self.running = True
        self.current_task = asyncio.create_task(self._loop())

    def stop(self):
        self.running = False
        if self.current_task:
            self.current_task.cancel()
