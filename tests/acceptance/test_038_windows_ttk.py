"""Feature 038 on the ttk window (audit v2): closing with the X during a task asks once, and only
then (AC-06, F1-01); an unexpected error during a task lands on Results with "Copy Details"
(AC-04, F1-02). Strings come from the catalog."""

from pathlib import Path

from support.flet_acceptance import QUIET
from support.gui_close import shut
from support.gui_fakes import FakeBackend, planned
from support.ttk_acceptance import Held
from support.ttk_unit import confirm, pump

from clearmd.backend.schemas.models import BatchPlan
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.intents.reset import unexpected
from clearmd.frontend.ttk import TtkApp
from clearmd.frontend.ttk.views.dialogs.confirm_close import ConfirmCloseDialog
from clearmd.i18n import load_catalog


def converting(tmp_path: Path, held: Held) -> TtkApp:
    plan = BatchPlan((planned("a.pdf", folder=tmp_path), planned("b.pdf", folder=tmp_path)), (), ())
    app = TtkApp(FakeBackend(plan=plan, settings=QUIET, before_finish=held))
    app.start()
    app.presenter.add_paths([tmp_path])
    app.presenter.analyze()
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    confirm(app)
    pump(app, until=held.started.is_set, seconds=5)
    assert app.presenter.state is AppState.CONVERTING
    return app


def press_x(app: TtkApp) -> None:
    """The window manager's close button: the window's WM_DELETE_WINDOW handler."""
    app.root.tk.call(app.root.protocol("WM_DELETE_WINDOW"))
    pump(app, seconds=0.1)


def alive(app: TtkApp) -> bool:
    try:
        return bool(app.root.winfo_exists())
    except Exception:  # noqa: BLE001 -- destroyed: Tk refuses the question
        return False


def test_ac_06_closing_during_a_task_asks_once(display: str, tmp_path: Path) -> None:
    held = Held()
    app = converting(tmp_path, held)
    catalog = load_catalog("en")
    try:
        press_x(app)
        dialog = app.dialog
        assert isinstance(dialog, ConfirmCloseDialog)
        assert dialog.title() == catalog.text("gui.close.title")
        assert dialog.keep.cget("text") == catalog.text("gui.close.keep")
        assert dialog.close_button.cget("text") == catalog.text("gui.close.close")
        dialog.event_generate("<Escape>")  # Esc: Keep Working, the default
        pump(app, until=lambda: app.dialog is None, seconds=1)
        assert app.presenter.state is AppState.CONVERTING and app.root.winfo_viewable()
        press_x(app)
        press_x(app)  # asked once: a second X while asking opens nothing more
        dialog = app.dialog
        assert isinstance(dialog, ConfirmCloseDialog)
        dialog.close_button.invoke()  # Close: cancel, hide, wait for the batch to end
        pump(app, seconds=0.1)
        assert not app.root.winfo_viewable()
        assert app.closing._closing_since is not None
    finally:
        held.gate.set()
        shut(app)
    idle = TtkApp(FakeBackend(settings=QUIET))
    idle.start()
    idle.root.tk.call(idle.root.protocol("WM_DELETE_WINDOW"))  # nothing running: no question
    assert idle.dialog is None and not alive(idle)  # it closed at once


def test_ac_04_an_error_during_a_task_shows_results(display: str, tmp_path: Path) -> None:
    held = Held()
    (tmp_path / "ClearMD_Output").mkdir()  # a folder that exists: it can be opened
    app = converting(tmp_path, held)
    catalog = load_catalog("en")
    try:
        unexpected(app.presenter._session, app.presenter._display, RuntimeError("boom"))
        pump(app, seconds=0.2)
        assert app.presenter.page == 4 and app.page is app.results
        assert app.presenter.state is AppState.FINISHED_WITH_PROBLEMS
        assert app.actions.details.winfo_ismapped()  # not cleared by the page change
        assert app.actions.details.cget("text") == catalog.text("gui.app.copy_details")
        assert app.actions.primary.cget("text") == catalog.text("gui.result.open")
        assert app.actions.primary.instate(["!disabled"])  # the folder exists
        assert catalog.text("gui.result.all_good") not in app.results.all_good_text.cget("text")
        assert app.message.cget("text") == catalog.text("gui.app.unexpected_error")
    finally:
        held.gate.set()
        shut(app)
