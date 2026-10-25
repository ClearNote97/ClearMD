"""A cancellation token: the interface sets it, the use cases honor it."""

import threading


class CancelToken:
    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    def is_set(self) -> bool:
        return self._event.is_set()

    def wait(self, timeout: float | None = None) -> bool:
        """Block until cancelled or ``timeout`` seconds pass; ``True`` if cancelled."""
        return self._event.wait(timeout)
