"""``View.after`` for Tk, safe from any thread (ADR-0026).

Tk may only be touched from the thread that created it. Callbacks from the worker thread go into
a queue that the UI thread empties every ``POLL_MS``; callbacks from the UI thread go to Tk at once.
"""

import queue
import threading
import tkinter as tk
from collections.abc import Callable

POLL_MS = 40


class Scheduler:
    def __init__(self, root: tk.Misc) -> None:
        self._root = root
        self._owner = threading.get_ident()
        self._queue: queue.SimpleQueue[tuple[int, Callable[[], None]]] = queue.SimpleQueue()
        self._closed = False
        self._pending: set[str] = set()  # Tk's ids of what is scheduled: cancelled on close
        self._schedule(POLL_MS, self._poll)

    def after(self, milliseconds: int, callback: Callable[[], None]) -> None:
        if self._closed:
            return
        if threading.get_ident() == self._owner:
            self._schedule(milliseconds, callback)
        else:
            self._queue.put((milliseconds, callback))

    def close(self) -> None:
        """Nothing scheduled runs after the window is gone."""
        self._closed = True
        for identifier in self._pending:
            try:
                self._root.after_cancel(identifier)
            except tk.TclError:
                pass
        self._pending.clear()

    def _schedule(self, milliseconds: int, callback: Callable[[], None]) -> None:
        holder: list[str] = []

        def run() -> None:
            self._pending.discard(holder[0])
            if not self._closed:
                callback()

        holder.append(self._root.after(max(0, milliseconds), run))
        self._pending.add(holder[0])

    def _poll(self) -> None:
        if self._closed:
            return
        while True:
            try:
                milliseconds, callback = self._queue.get_nowait()
            except queue.Empty:
                break
            self._schedule(milliseconds, callback)
        self._schedule(POLL_MS, self._poll)
