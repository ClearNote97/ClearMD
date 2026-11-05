"""Shared helpers of the feature 005 acceptance tests (the ttk window driven with fakes)."""

import shutil
import threading
import time
from collections.abc import Callable, Iterator
from dataclasses import replace
from pathlib import Path
from typing import Any

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.presenter import AppState
from clearmd.frontend.ttk import TtkApp
from support import DOCUMENTS_DIR

ROOT = Path(__file__).resolve().parents[2]
QUIET = Settings(show_welcome=False, open_output_when_done=False)


def pump(app: TtkApp, *, until: Callable[[], bool] | None = None, seconds: float = 5.0) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        app.root.update()
        if until is not None and until():
            return
        time.sleep(0.01)


def confirm(app: TtkApp) -> None:
    """Convert the plan: Next on Review, then Convert (ADR-0029)."""
    if app.presenter.page == 2:
        app.actions.primary.invoke()
        pump(app, until=lambda: app.presenter.page == 3, seconds=10)
    app.actions.primary.invoke()


def convert_more(app: TtkApp, *, keep: bool = True) -> None:
    from clearmd.frontend.ttk.views.dialogs.keep_inputs import KeepInputsDialog

    app.actions.secondary.invoke()
    assert isinstance(app.dialog, KeepInputsDialog)
    app.dialog.answer(keep)


def press_enter(app: TtkApp) -> None:
    """Enter on the window: it needs the keyboard focus first (Windows gives it only on demand)."""
    app.root.focus_force()
    app.root.update()
    app.root.event_generate("<KeyPress-Return>", when="tail")
    app.root.event_generate("<KeyRelease-Return>", when="tail")  # pressed and let go


def to_review(app: TtkApp, *paths: Path) -> None:
    app.presenter.add_paths(list(paths))
    app.actions.primary.invoke()
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION, seconds=60)


def converted(app: TtkApp) -> bool:
    return app.presenter.state in {
        AppState.FINISHED,
        AppState.FINISHED_WITH_PROBLEMS,
        AppState.CANCELLED,
    }


def copy_documents(folder: Path, *names: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    for name in names:
        shutil.copyfile(DOCUMENTS_DIR / name, folder / name)
    return folder


def widgets(root: Any) -> Iterator[Any]:
    pending = [root]
    while pending:
        widget = pending.pop()
        yield widget
        pending.extend(widget.winfo_children())


class Held:
    """Holds the batch on its first file until released."""

    def __init__(self) -> None:
        self.gate, self.started = threading.Event(), threading.Event()

    def __call__(self) -> None:
        self.started.set()
        self.gate.wait(10)


def replace_settings(settings: Settings, **changes: Any) -> Settings:
    return replace(settings, **changes)
