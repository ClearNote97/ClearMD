"""Shared helpers of the feature 018 acceptance tests: the flet window on a page that is not flet's.

flet's controls are plain objects: the window is built and driven here without flet's program
(no screen, no network, nothing downloaded). ``FakePage`` (``flet_fake_page``) stands for the page.
"""

import dataclasses
import shutil
import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, cast

import flet as ft

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.flet import FletApp
from clearmd.frontend.presenter import AppState
from support import DOCUMENTS_DIR
from support.flet_fake_page import FakePage

ROOT = Path(__file__).resolve().parents[2]
QUIET = Settings(show_welcome=False, open_output_when_done=False)
CLOSE_SECONDS = 30.0
Window = Callable[..., FletApp]


def page_of(app: FletApp) -> FakePage:
    page = app.page
    assert isinstance(page, FakePage)
    return page


def pump(app: FletApp, *, until: Callable[[], bool] | None = None, seconds: float = 5.0) -> None:
    """Run the page's loop until ``until`` holds or ``seconds`` pass."""
    page = page_of(app)
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        page.run_due()
        if until is not None and until():
            return
        time.sleep(0.005)


def open_window(backend: Any) -> FletApp:
    app = FletApp(FakePage(), backend)
    app.start()
    pump(app, seconds=0.05)
    return app


def shut(app: FletApp) -> None:
    """Close for sure: a window closed while converting waits for the batch."""
    app.close()
    pump(app, until=lambda: app.closing.closed, seconds=CLOSE_SECONDS)
    if not app.closing.closed:
        app.closing.destroy()


def windows() -> Iterator[Window]:
    """The body of a ``flet_window`` fixture: opens windows, closes every one at the end."""
    opened: list[FletApp] = []

    def make(backend: Any) -> FletApp:
        app = open_window(backend)
        opened.append(app)
        return app

    yield make
    for app in opened:
        try:
            shut(app)
        except Exception:  # noqa: BLE001 -- already closed by the test
            pass


def click(control: ft.BaseControl) -> None:
    """A click (or a box ticked): the control's handler, as flet calls it (no event). A disabled
    control takes no click, as on screen."""
    handler = getattr(control, "on_click", None) or getattr(control, "on_change", None)
    assert handler is not None, control
    if not getattr(control, "disabled", False):
        cast(Callable[[], object], handler)()


def walk(control: ft.BaseControl, *, visible: bool = False) -> Iterator[ft.BaseControl]:
    """``control`` and every control inside it; ``visible``: only what is on screen."""
    if visible and not getattr(control, "visible", True):
        return
    yield control
    for field in dataclasses.fields(control):
        if field.name.startswith("_"):
            continue
        value = getattr(control, field.name, None)
        for child in value if isinstance(value, list) else [value]:
            if isinstance(child, ft.BaseControl):
                yield from walk(child, visible=visible)


def texts(control: ft.BaseControl) -> list[str]:
    return [str(c.value) for c in walk(control) if isinstance(c, ft.Text) and c.value]


def to_review(app: FletApp, *paths: Path) -> None:
    app.presenter.add_paths(list(paths))
    click(app.actions.primary)
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION, seconds=60)


def confirm(app: FletApp) -> None:
    """Convert the plan: Next on Review, then Convert (ADR-0029)."""
    if app.presenter.page == 2:
        click(app.actions.primary)
        pump(app, until=lambda: app.presenter.page == 3, seconds=10)
    click(app.actions.primary)


def converted(app: FletApp) -> bool:
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


class Held:
    """Holds the batch on its first file until released."""

    def __init__(self) -> None:
        self.gate, self.started = threading.Event(), threading.Event()

    def __call__(self) -> None:
        self.started.set()
        self.gate.wait(10)
