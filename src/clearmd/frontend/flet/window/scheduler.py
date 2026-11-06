"""``View.after`` for flet, safe from any thread (ADR-0038).

The page's port queues the work to flet's loop (``PagePort.post``); this adds the one thing the
window owns: once it is closed, nothing scheduled runs. A module of its own, so a test page can
run the work on the test's own thread.
"""

from collections.abc import Callable


class Scheduler:
    def __init__(self, post: Callable[[float, Callable[[], None]], None]) -> None:
        self._post = post
        self.closed = False

    def after(self, milliseconds: int, callback: Callable[[], None]) -> None:
        self._post(milliseconds / 1000, lambda: self._run(callback))

    def close(self) -> None:
        """Nothing scheduled runs after the window is gone."""
        self.closed = True

    def _run(self, callback: Callable[[], None]) -> None:
        if not self.closed:
            callback()
