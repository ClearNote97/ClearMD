"""``View.after`` for Qt, safe from any thread (ADR-0038).

Work comes back from the worker thread through a signal: Qt queues it to the UI thread, and a
timer there waits out the delay. A module of its own: the queued-signal bridge is Qt-only.
"""

from collections.abc import Callable

from PySide6.QtCore import QObject, Qt, QTimer, Signal


class Scheduler(QObject):
    """From any thread to the UI thread: a queued signal, then a timer for the delay."""

    later = Signal(int, object)

    def __init__(self) -> None:
        super().__init__()
        self.later.connect(self._schedule, Qt.ConnectionType.QueuedConnection)
        self.closed = False

    def after(self, milliseconds: int, callback: Callable[[], None]) -> None:
        self.later.emit(milliseconds, callback)

    def close(self) -> None:
        """Nothing scheduled runs after the window is gone."""
        self.closed = True

    def _schedule(self, milliseconds: int, callback: Callable[[], None]) -> None:
        if not self.closed:
            QTimer.singleShot(milliseconds, self, lambda: self._run(callback))

    def _run(self, callback: Callable[[], None]) -> None:
        if not self.closed:
            callback()
