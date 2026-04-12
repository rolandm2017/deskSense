from __future__ import annotations

import asyncio


class TaskRegistry:
    """Tracks asyncio tasks created on behalf of a specific owner so that
    shutdown can cancel exactly those tasks — no scanning, no guessing.
    """

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop
        self.tasks: list[asyncio.Task] = []

    def create_task(self, coro, *, name: str) -> asyncio.Task:
        self._prune_done()
        task = self._loop.create_task(coro, name=name)
        self.tasks.append(task)
        task.add_done_callback(self._discard_task)
        return task

    async def cancel_all(self, timeout: float = 3.0) -> int:
        self._prune_done()
        pending = [t for t in self.tasks if not t.done()]
        if not pending:
            return 0

        for task in pending:
            task.cancel()

        try:
            await asyncio.wait_for(
                asyncio.gather(*pending, return_exceptions=True),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            pass

        self._prune_done()
        return len(pending)

    def _discard_task(self, task: asyncio.Task) -> None:
        try:
            self.tasks.remove(task)
        except ValueError:
            pass

    def _prune_done(self) -> None:
        self.tasks = [task for task in self.tasks if not task.done()]
