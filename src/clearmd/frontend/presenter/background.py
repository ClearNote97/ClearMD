"""Work off the UI thread and its way back: what a stale generation returns is dropped."""

import threading
from collections.abc import Callable

from clearmd.frontend.presenter.ports import View
from clearmd.frontend.presenter.session import Session


def in_background(work: Callable[[], None]) -> None:
    threading.Thread(target=work, name="clearmd-work", daemon=True).start()


class Background:
    def __init__(
        self, view: View, session: Session, spawn: Callable[[Callable[[], None]], None] | None
    ) -> None:
        self._view = view
        self._session = session
        self.spawn = spawn or in_background

    def later(self, generation: int, callback: Callable[[], None]) -> None:
        """From the worker thread: run ``callback`` on the UI thread, unless it is stale."""

        def guarded() -> None:
            if generation == self._session.generation:
                callback()

        self._view.after(0, guarded)

    def next_generation(self) -> int:
        self._session.generation += 1
        return self._session.generation
