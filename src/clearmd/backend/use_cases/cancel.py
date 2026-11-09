"""A cancellation token: the interface sets it, the use cases honor it. It travels with every
job, so it also carries where a job's progress goes (audit 2026-11-08, 3B)."""

import threading
from collections.abc import Callable


class CancelToken:
    def __init__(self) -> None:
        self._event = threading.Event()
        self._progress: Callable[[int, int], None] | None = None

    def on_progress(self, listener: Callable[[int, int], None] | None) -> None:
        """Who hears "page 40 of 120" for the job about to run (``None``: nobody)."""
        self._progress = listener

    def progress(self, done: int, total: int) -> None:
        if self._progress is not None:
            self._progress(done, total)

    def cancel(self) -> None:
        self._event.set()

    def is_set(self) -> bool:
        return self._event.is_set()

    def wait(self, timeout: float | None = None) -> bool:
        """Block until cancelled or ``timeout`` seconds pass; ``True`` if cancelled."""
        return self._event.wait(timeout)
