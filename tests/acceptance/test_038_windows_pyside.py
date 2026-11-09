"""Feature 038 in the PySide6 window (audit v2): closing the window during a task asks once, and
only then (AC-06); an unexpected error during a task lands on Results with "Copy Details" and the
results folder (AC-04). Strings come from the catalog."""

from collections.abc import Callable
from pathlib import Path

from support.gui_fakes import FakeBackend, planned
from support.pyside_acceptance import (
    QUIET,
    Held,
    confirm,
    converted,
    pump,
    to_review,
)

from clearmd.backend.schemas.models import BatchPlan
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.intents.reset import unexpected
from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.pyside import PySideApp
from clearmd.frontend.pyside.views.dialogs.confirm_close import ConfirmCloseDialog
from clearmd.i18n import load_catalog

Window = Callable[..., PySideApp]


def converting(qt_window: Window, folder: Path) -> tuple[PySideApp, Held]:
    held = Held()
    plan = BatchPlan((planned("a.pdf", folder=folder),), (), ())  # its results under the folder
    app = qt_window(FakeBackend(settings=QUIET, plan=plan, before_finish=held))
    app.presenter.choose_tool(Tool.CONVERT)
    to_review(app, folder)
    confirm(app)
    pump(app, until=held.started.is_set)
    pump(app, seconds=0.05)
    assert app.presenter.state is AppState.CONVERTING
    return app, held


def test_ac_06_closing_during_a_task_asks_once(qt_window: Window, tmp_path: Path) -> None:
    app, held = converting(qt_window, tmp_path)
    catalog = load_catalog("en")
    app.window.close()  # the window's X
    pump(app, seconds=0.05)
    dialog = app.dialogs.current
    assert isinstance(dialog, ConfirmCloseDialog)
    assert dialog.windowTitle() == catalog.text("gui.close.title")
    assert dialog.keep.text() == catalog.text("gui.close.keep") and dialog.keep.isDefault()
    assert dialog.close_window.text() == catalog.text("gui.close.close")
    app.window.close()  # asked once: no second question
    assert app.dialogs.current is dialog
    dialog.keep.click()  # Keep Working: the task goes on
    pump(app, seconds=0.05)
    assert app.dialogs.current is None and not app.closing.closed
    assert app.presenter.state is AppState.CONVERTING and app.window.isVisible()
    app.window.close()
    again = app.dialogs.current
    assert isinstance(again, ConfirmCloseDialog)
    again.close_window.click()  # Close: cancel, then wait for the batch's end
    held.gate.set()
    pump(app, until=lambda: app.closing.closed, seconds=10)
    assert app.closing.closed


def test_ac_06_closing_when_idle_never_asks(qt_window: Window) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    app.window.close()
    pump(app, until=lambda: app.closing.closed, seconds=5)
    assert app.closing.closed and app.dialogs.current is None


def test_ac_06_cancel_never_asks(qt_window: Window, tmp_path: Path) -> None:
    app, held = converting(qt_window, tmp_path)
    app.actions.secondary.click()  # the action bar's Cancel
    assert app.dialogs.current is None
    held.gate.set()
    pump(app, until=lambda: converted(app), seconds=10)


def test_ac_04_an_error_during_a_task_shows_results(qt_window: Window, tmp_path: Path) -> None:
    app, held = converting(qt_window, tmp_path)
    catalog = load_catalog("en")
    folder = tmp_path / "ClearMD_Output"
    folder.mkdir(exist_ok=True)
    unexpected(app.presenter._session, app.presenter._display, RuntimeError("boom"))  # noqa: SLF001
    pump(app, seconds=0.8)  # past the primary action's pause after a page change (F-1)
    assert app.presenter.page == 4 and app.results.isVisible()
    assert app.presenter.state is AppState.FINISHED_WITH_PROBLEMS
    assert app.message.text() == catalog.text("gui.app.unexpected_error")
    assert app.details.isVisible() and app.details.text() == catalog.text("gui.app.copy_details")
    assert app.actions.primary.text() == catalog.text("gui.result.open")
    assert app.actions.primary.isEnabled()
    held.gate.set()
    pump(app, seconds=0.3)
