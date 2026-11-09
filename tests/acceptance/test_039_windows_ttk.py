"""Feature 039 on the ttk window (audit v3): one keyboard rule (AC-10: Enter on a button presses
it, in a field confirms the field, only otherwise the primary action; Delete and Ctrl+A act on
the list only while it has the focus), a selected row keeps its tone (AC-07), Clear All apart, and
Settings fits a 1366 × 768 screen (AC-09)."""

import time
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

from support.flet_acceptance import QUIET
from support.gui_close import shut
from support.gui_fakes import FakeBackend, planned
from support.ttk_unit import confirm, pump

from clearmd.backend.schemas.models import BatchPlan, OutcomeStatus
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.ttk import TtkApp
from clearmd.frontend.ttk.views.dialogs.settings import SettingsDialog
from clearmd.frontend.ttk.views.dialogs.welcome import WelcomeDialog
from clearmd.i18n import load_catalog

DOCS = Path("/docs")
PLAN = BatchPlan((planned("a.pdf"), planned("b.docx")), (), ())


def focus(app: TtkApp, widget: Any) -> None:
    app.root.deiconify()
    widget.focus_force()
    pump(app, until=lambda: app.root.focus_get() is widget, seconds=2)
    assert app.root.focus_get() is widget


def key(app: TtkApp, widget: Any, name: str) -> None:
    """A key pressed and let go on ``widget`` (it has the focus); then past the F-1 pause."""
    widget.event_generate(f"<KeyPress-{name}>", when="tail")
    widget.event_generate(f"<KeyRelease-{name}>", when="tail")
    pump(app, seconds=0.2)


def test_ac_10_keyboard_enter_on_back_does_not_convert(window: Callable[..., TtkApp]) -> None:
    app = window(FakeBackend(plan=PLAN, settings=QUIET))
    app.presenter.add_paths([DOCS])
    app.presenter.analyze()
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    time.sleep(0.6)  # past the primary's pause after the page change
    back = app.actions.secondary
    focus(app, back)
    key(app, back, "Return")
    assert app.presenter.page == 1 and app.presenter.state is AppState.WAITING_DECISION


def test_ac_10_keyboard_enter_in_a_number_field_does_not_convert(
    window: Callable[..., TtkApp],
) -> None:
    app = window(FakeBackend(plan=PLAN, settings=QUIET))
    app.presenter.choose_tool(Tool.SPLIT)
    app.presenter.add_paths([DOCS])
    pump(app, seconds=0.6)
    field = app.main.split.numbers["parts"]
    focus(app, field)
    field.delete(0, "end")
    field.insert(0, "3")
    key(app, field, "Return")
    assert app.presenter.settings.split_parts == 3  # the field is confirmed…
    assert app.presenter.page == 1 and app.presenter.state is AppState.READY  # …nothing more


def test_ac_10_keyboard_delete_and_ctrl_a_in_a_number_field_leave_the_list(
    window: Callable[..., TtkApp],
) -> None:
    app = window(FakeBackend(plan=PLAN, settings=QUIET))
    app.presenter.choose_tool(Tool.SPLIT)
    app.presenter.add_paths([DOCS / "a.pdf", DOCS / "b.pdf"])
    pump(app, seconds=0.3)
    tree = app.main.inputs.tree
    tree.selection_set(tree.get_children()[0])
    field = app.main.split.numbers["pages"]
    focus(app, field)
    key(app, field, "Delete")
    field.event_generate("<Control-a>", when="tail")
    pump(app, seconds=0.1)
    assert app.main.inputs.names() == ["a.pdf", "b.pdf"]  # Delete removed nothing
    assert len(tree.selection()) == 1  # Ctrl+A checked nothing in the list


def test_ac_10_keyboard_enter_with_the_list_focused_runs_the_primary(
    window: Callable[..., TtkApp],
) -> None:
    app = window(FakeBackend(plan=PLAN, settings=QUIET))
    app.presenter.go_to(1)
    app.presenter.add_paths([DOCS])
    time.sleep(0.6)
    tree = app.main.inputs.tree
    focus(app, tree)
    key(app, tree, "Return")
    pump(app, until=lambda: app.presenter.page == 2)
    assert app.presenter.page == 2  # Next


def test_ac_07_a_selected_row_keeps_its_tone(window: Callable[..., TtkApp]) -> None:
    statuses = {"a.pdf": OutcomeStatus.FAILED}
    app = window(FakeBackend(plan=PLAN, settings=QUIET, statuses=statuses))
    app.presenter.add_paths([DOCS])
    app.presenter.analyze()
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    confirm(app)
    pump(app, until=lambda: app.presenter.page == 4)
    pump(app, seconds=0.1)
    files = app.results.problems
    assert files.tree.selection() == ()  # Results never pre-selects a row
    item = files.tree.get_children()[0]
    files.tree.selection_set(item)
    pump(app, seconds=0.1)
    shown = files.pictures._shown[item]  # the row's picture: its number in the tone's colour
    assert shown[-1] == app.palette.danger
    assert files.tree.item(item, "tags") == ("danger",)


def test_ac_10_clear_all_stands_apart(window: Callable[..., TtkApp]) -> None:
    app = window(FakeBackend(plan=PLAN, settings=QUIET))
    app.presenter.go_to(1)
    app.presenter.add_paths([DOCS])
    pump(app, seconds=0.3)
    main = app.main
    clear, deselect = main.clear.winfo_rootx(), main.deselect.winfo_rootx()
    divider = main._inputs_card.divider
    assert divider.winfo_ismapped()
    assert deselect < divider.winfo_rootx() < clear  # a divider between them, Clear All last


def test_ac_09_settings_fits_a_1366_by_768_screen(window: Callable[..., TtkApp]) -> None:
    app = window(FakeBackend(settings=QUIET))
    app.root.geometry("1366x728+0+0")  # the window filling a 1366 × 768 screen with a taskbar
    app.presenter.go_to(1)
    pump(app, seconds=0.3)
    app.rail.settings.invoke()
    pump(app, seconds=0.3)
    dialog = app.dialog
    assert isinstance(dialog, SettingsDialog)
    bottom = dialog.actions.winfo_rooty() + dialog.actions.winfo_height()
    assert dialog.winfo_rooty() >= 0 and bottom <= 768  # Save and Cancel on the screen
    dialog.close()


def test_ac_10_undo_gives_the_list_back(window: Callable[..., TtkApp]) -> None:
    app = window(FakeBackend(plan=PLAN, settings=QUIET))
    catalog = load_catalog("en")
    app.presenter.choose_tool(Tool.MERGE)
    app.presenter.add_paths([DOCS / "a.md", DOCS / "b.md", DOCS / "c.md"])
    pump(app, seconds=0.2)
    tree = app.main.inputs.tree
    tree.selection_set(tree.get_children()[2])
    pump(app, seconds=0.05)
    app.main.move_up.invoke()  # Merge's order: a, c, b
    pump(app, seconds=0.2)
    order = app.main.inputs.names()
    assert order == ["a.md", "c.md", "b.md"]
    app.main.clear.invoke()
    pump(app, seconds=0.2)
    undo = app.actions.undo
    assert app.main.inputs.names() == []
    assert app.message.cget("text") == catalog.text("gui.main.cleared", count=3)
    assert undo.winfo_ismapped() and undo.cget("text") == catalog.text("gui.main.undo")
    assert undo.winfo_height() >= 44 and undo.cget("takefocus") != 0  # a target, reachable
    undo.invoke()
    pump(app, seconds=0.2)
    assert app.main.inputs.names() == order  # the list is back, in its order
    assert not undo.winfo_manager() and app.message.cget("text") == ""


def test_ac_04_the_welcome_switches_the_language(display: str) -> None:
    app = TtkApp(FakeBackend(settings=replace(QUIET, show_welcome=True)))
    app.start()
    try:
        pump(app, until=lambda: app.dialog is not None)
        dialog = app.dialog
        assert isinstance(dialog, WelcomeDialog)
        en, es = load_catalog("en"), load_catalog("es")
        assert dialog.languages["es"].cget("text") == es.text("gui.welcome.language_es")
        dialog.languages["es"].invoke()  # "Español", while the Welcome is open
        pump(app, seconds=0.2)
        assert app.presenter.settings.language == "es"
        assert app.dialog is dialog and dialog.title() == es.text("gui.welcome.title")
        assert [line.cget("text") for line in dialog.steps] == [
            es.text(f"gui.welcome.step{n}") for n in (1, 2, 3)
        ]
        dialog.languages["en"].invoke()
        pump(app, seconds=0.2)
        assert dialog.title() == en.text("gui.welcome.title")
        dialog.close()
    finally:
        shut(app)


def test_ac_04_results_say_how_to_use_it(window: Callable[..., TtkApp], tmp_path: Path) -> None:
    plan = BatchPlan((planned("a.pdf", folder=tmp_path),), (), ())
    app = window(FakeBackend(plan=plan, settings=QUIET))
    app.presenter.add_paths([tmp_path])
    app.presenter.analyze()
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    confirm(app)
    pump(app, until=lambda: app.presenter.page == 4)
    pump(app, seconds=0.1)
    assert app.last_result is not None and app.last_result.with_ai
    line = app.results.with_ai
    assert line.winfo_ismapped() and line.cget("text") == app.last_result.with_ai
    assert line.cget("text") == load_catalog("en").text("gui.result.with_ai")
