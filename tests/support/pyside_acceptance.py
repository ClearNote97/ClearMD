"""Shared helpers of the feature 016 acceptance tests: the PySide6 window, offscreen, driven with
fakes. Qt reads ``QT_QPA_PLATFORM`` when it loads: importing this module first is enough."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # before Qt is loaded: no display needed

import shutil  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402
from collections.abc import Callable  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402

from PySide6.QtCore import QMimeData, QPointF, Qt, QUrl  # noqa: E402
from PySide6.QtGui import QDropEvent  # noqa: E402
from PySide6.QtTest import QTest  # noqa: E402
from PySide6.QtWidgets import QApplication, QWidget  # noqa: E402

from clearmd.backend.schemas.settings import Settings  # noqa: E402
from clearmd.frontend.presenter import AppState  # noqa: E402
from clearmd.frontend.pyside import PySideApp  # noqa: E402
from clearmd.frontend.pyside.window.toolkit import application  # noqa: E402
from support import DOCUMENTS_DIR  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
QUIET = Settings(show_welcome=False, open_output_when_done=False)
CLOSE_SECONDS = 30.0


def pump(app: PySideApp, *, until: Callable[[], bool] | None = None, seconds: float = 5.0) -> None:
    """Run Qt's event loop until ``until`` holds or ``seconds`` pass."""
    qt = application()
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        qt.processEvents()
        if until is not None and until():
            return
        time.sleep(0.01)


def open_window(backend: Any) -> PySideApp:
    app = PySideApp(backend)
    app.start()
    app.window.activateWindow()
    pump(app, seconds=0.1)
    return app


def shut(app: PySideApp) -> None:
    """Close for sure: a window closed while converting waits for the batch, an event loop gets it
    there."""
    app.close()
    pump(app, until=lambda: app.closing.closed, seconds=CLOSE_SECONDS)
    if not app.closing.closed:
        app.closing.destroy()
    application().processEvents()


def press(
    app: PySideApp, key: Qt.Key, modifier: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier
) -> None:
    """A key pressed and let go where the keyboard focus is (the window's shortcuts still apply:
    the window must be active)."""
    app.window.activateWindow()
    QTest.keyClick(QApplication.focusWidget() or app.window, key, modifier)
    pump(app, seconds=0.02)


def drop(app: PySideApp, *paths: Path) -> None:
    """Files dropped on the window, as the desktop does it."""
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(path)) for path in paths])
    event = QDropEvent(
        QPointF(40, 40),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    app.window.dropEvent(event)


def confirm(app: PySideApp) -> None:
    """Convert the plan: Next on Review, then Convert (ADR-0029)."""
    if app.presenter.page == 2:
        app.actions.primary.click()
        pump(app, until=lambda: app.presenter.page == 3, seconds=10)
    app.actions.primary.click()


def to_review(app: PySideApp, *paths: Path) -> None:
    app.presenter.add_paths(list(paths))
    app.actions.primary.click()
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION, seconds=60)


def converted(app: PySideApp) -> bool:
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


def descendants(root: QWidget) -> list[QWidget]:
    return [root, *root.findChildren(QWidget)]


class Held:
    """Holds the batch on its first file until released."""

    def __init__(self) -> None:
        self.gate, self.started = threading.Event(), threading.Event()

    def __call__(self) -> None:
        self.started.set()
        self.gate.wait(10)
