"""Fakes of the presenter unit tests: a view that records what is shown, a clock, builders."""

import os
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from clearmd.frontend.presenter import Presenter
from clearmd.i18n import Catalog
from support.gui_fakes import FakeBackend


def absolute(path: str) -> Path:
    """How the presenter keeps an input: absolute (on Windows, with the current drive)."""
    return Path(os.path.abspath(path))


@dataclass
class FakeView:
    """Records what the presenter shows; callbacks scheduled with ``after`` run when drained."""

    calls: list[tuple[str, Any]] = field(default_factory=list)
    pending: list[tuple[int, Callable[[], None]]] = field(default_factory=list)
    threads: list[int] = field(default_factory=list)

    def after(self, milliseconds: int, callback: Callable[[], None]) -> None:
        self.pending.append((milliseconds, callback))

    def drain(self, *, timers: bool = False) -> None:
        """Run the scheduled callbacks (the UI loop); timers (ms > 0) only when asked."""
        while True:
            ready = [entry for entry in self.pending if timers or entry[0] == 0]
            if not ready:
                return
            for entry in ready:
                self.pending.remove(entry)
                entry[1]()
            if timers:
                return

    def last(self, name: str) -> Any:
        return next(value for call, value in reversed(self.calls) if call == name)

    def _record(self, name: str, value: Any) -> None:
        self.threads.append(threading.get_ident())
        self.calls.append((name, value))

    def show_state(self, state: Any) -> None:
        self._record("state", state)

    def show_inputs(self, rows: Any) -> None:
        self._record("inputs", rows)

    def show_output_choice(self, choice: Any) -> None:
        self._record("output", choice)

    def show_scan(self, text: str) -> None:
        self._record("scan", text)

    def show_details_button(self, label: str | None) -> None:
        self._record("details_button", label)

    def copy_text(self, text: str) -> None:
        self._record("copied", text)

    def show_plan(self, plan: Any) -> None:
        self._record("plan", plan)

    def show_progress(self, progress: Any) -> None:
        self._record("progress", progress)

    def show_result(self, result: Any) -> None:
        self._record("result", result)

    def show_message(self, text: str) -> None:
        self._record("message", text)

    def show_welcome(self, steps: Any) -> None:
        self._record("welcome", steps)

    def forget_work(self) -> None:
        self._record("forget", None)

    def apply_theme(self, theme: str) -> None:
        self._record("theme", theme)

    def apply_language(self, catalog: Catalog) -> None:
        self._record("language", catalog.language)


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def make(
    backend: FakeBackend | None = None, *, threaded: bool = False, theme: str = "dark"
) -> tuple[Presenter, FakeView, FakeBackend, Clock]:
    view, fake, clock = FakeView(), backend or FakeBackend(), Clock()
    spawn: Callable[[Callable[[], None]], None] | None = None if threaded else (lambda work: work())
    presenter = Presenter(view, fake, clock=clock, detect_theme=lambda: theme, spawn=spawn)
    presenter.start()
    view.drain()
    return presenter, view, fake, clock


def converted(backend: FakeBackend | None = None) -> tuple[Presenter, FakeView, FakeBackend, Clock]:
    presenter, view, fake, clock = make(backend)
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    presenter.confirm()
    view.drain()
    return presenter, view, fake, clock


def state(view: FakeView) -> Any:
    return view.last("state")
