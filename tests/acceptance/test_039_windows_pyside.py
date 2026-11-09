"""Feature 039 in the PySide6 window (audit v3): one keyboard rule (AC-10), Clear All apart (AC-10),
a selected row keeps its tone and Results never chooses a row (AC-07), and Settings fits a
1366 x 768 screen with Save at the foot (AC-09); brief B: Undo after Clear All (AC-10), the
Welcome's language buttons and Results' line about using the result (AC-04). Strings come from
the catalog."""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor
from support.gui_fakes import FakeBackend, MemoryBackend, planned
from support.pyside_acceptance import QUIET, confirm, converted, press, pump, to_review

import clearmd.frontend.pyside.components.dialog as dialog_module
from clearmd.backend.schemas.models import BatchPlan, OutcomeStatus
from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.pyside import PySideApp
from clearmd.frontend.pyside.views.dialogs.settings import SettingsDialog
from clearmd.frontend.pyside.views.dialogs.welcome import WelcomeDialog
from clearmd.i18n import load_catalog

Window = Callable[..., PySideApp]
LAPTOP = 768 - 40  # a 1366 x 768 screen less a 40 px taskbar: the room a window has


def on_step_1(app: PySideApp, folder: Path, tool: Tool = Tool.CONVERT) -> None:
    app.presenter.choose_tool(tool)
    app.presenter.add_paths([folder])
    pump(app, seconds=0.05)


def test_ac_10_keyboard_enter_on_back_does_not_convert(qt_window: Window, tmp_path: Path) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    app.presenter.choose_tool(Tool.CONVERT)
    to_review(app, tmp_path)
    app.presenter.go_to(3)
    pump(app, seconds=0.8)  # past the primary action's pause (F-1)
    back = app.actions.secondary
    assert back.isVisible() and back.text() == load_catalog("en").text("gui.plan.back")
    back.setFocus()
    press(app, Qt.Key.Key_Return)  # Enter on a button presses that button
    assert app.presenter.page == 2 and app.presenter.state is AppState.WAITING_DECISION


def test_ac_10_keyboard_enter_in_a_number_field_does_not_convert(
    qt_window: Window, tmp_path: Path
) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    on_step_1(app, tmp_path, Tool.SPLIT)
    box = app.main.split.parts
    box.setFocus()
    box.lineEdit().setText("3")
    press(app, Qt.Key.Key_Return)  # in a field, Enter confirms the field
    assert app.presenter.page == 1 and app.presenter.state is AppState.READY
    assert app.presenter.settings.split_parts == 3


def test_ac_10_keyboard_delete_and_ctrl_a_in_a_number_field_leave_the_list(
    qt_window: Window, tmp_path: Path
) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    on_step_1(app, tmp_path, Tool.SPLIT)
    rows = app.main.inputs.rows()
    app.main.inputs.select(0)
    app.main.split.pages.setFocus()
    press(app, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    press(app, Qt.Key.Key_Delete)
    assert app.main.inputs.rows() == rows  # the list is untouched


def test_ac_10_keyboard_enter_with_the_list_focused_runs_the_primary(
    qt_window: Window, tmp_path: Path
) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    on_step_1(app, tmp_path)
    pump(app, seconds=0.8)
    app.main.inputs.tree.setFocus()
    press(app, Qt.Key.Key_Return)
    pump(app, until=lambda: app.presenter.page == 2, seconds=5)
    assert app.presenter.page == 2


def test_ac_10_clear_all_stands_apart_from_deselect_all(qt_window: Window, tmp_path: Path) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    on_step_1(app, tmp_path)
    catalog = load_catalog("en")
    clear, deselect = app.main.clear, app.main.deselect
    assert clear.text() == catalog.text("gui.main.clear")
    gap = clear.mapTo(app.window, QPoint(0, 0)).x() - (
        deselect.mapTo(app.window, QPoint(0, 0)).x() + deselect.width()
    )
    assert gap > 4 * 8  # well apart, at the other end of the row


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_ac_07_a_selected_row_keeps_its_tone(qt_window: Window, tmp_path: Path, theme: str) -> None:
    plan = BatchPlan((planned("a.pdf"), planned("bad.pdf")), (), ())
    fake = FakeBackend(
        settings=replace(QUIET, theme=theme), plan=plan, statuses={"bad.pdf": OutcomeStatus.FAILED}
    )
    app = qt_window(fake)
    app.presenter.choose_tool(Tool.CONVERT)
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=lambda: converted(app) and app.presenter.page == 4, seconds=10)
    problems = app.results.problems
    assert problems.selected_indexes() == []  # Results never chooses a row
    problems.select(0)
    pump(app, seconds=0.05)
    tree = problems.tree
    item = tree.topLevelItem(0)
    assert item is not None and item.isSelected()
    cell = tree.visualRect(tree.indexFromItem(item, 2))  # the detail, in the danger tone
    image = tree.viewport().grab().toImage()
    danger = QColor(app.shown.palette.danger)
    found = any(
        QColor(image.pixel(x, y)) == danger
        for x in range(cell.left(), cell.right())
        for y in range(cell.top(), cell.bottom())
    )
    assert found


def test_ac_09_settings_fits_a_1366_x_768_screen(
    qt_window: Window, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        dialog_module, "screen_room", lambda _w: LAPTOP - dialog_module.SCREEN_MARGIN
    )
    app = qt_window(FakeBackend(settings=replace(QUIET, language="es")))
    app.rail.settings.click()
    pump(app, seconds=0.2)
    dialog = app.dialogs.current
    assert isinstance(dialog, SettingsDialog)
    assert dialog.height() <= LAPTOP
    assert dialog.area.verticalScrollBar().maximum() > 0  # the settings scroll
    save = next(
        b for b in dialog.findChildren(type(app.actions.primary)) if b.objectName() == "primary"
    )
    bottom = save.mapTo(dialog, QPoint(0, save.height())).y()
    assert save.isVisible() and bottom <= dialog.height()  # Save at the foot, on screen
    dialog.close_dialog()


def test_ac_10_undo_gives_the_list_back(qt_window: Window, tmp_path: Path) -> None:
    names = ("a.md", "b.md", "c.md")
    for name in names:
        (tmp_path / name).write_text(f"{name}\n", "utf-8")
    app = qt_window(FakeBackend(settings=QUIET))
    app.presenter.choose_tool(Tool.MERGE)
    app.presenter.add_paths([tmp_path / name for name in names])
    pump(app, seconds=0.05)
    app.main.order.arrows[2][-1].click()  # Merge's own order: c before b
    order = [row.name for row in app.main.inputs.rows()]
    assert order == ["a.md", "c.md", "b.md"]
    catalog = load_catalog("en")
    app.main.clear.click()
    assert app.main.inputs.rows() == ()
    undo = app.undo
    assert undo.isVisible() and undo.text() == catalog.text("gui.main.undo")
    assert undo.height() >= 44 and undo.focusPolicy() is not Qt.FocusPolicy.NoFocus
    assert app.message.text() == catalog.text("gui.main.cleared", count=3)
    undo.click()
    assert [row.name for row in app.main.inputs.rows()] == order  # the list and its order
    assert not undo.isVisible() and app.message.text() == ""


def test_ac_04_the_welcome_switches_the_language(qt_window: Window) -> None:
    backend = MemoryBackend(Settings())  # first run: the Welcome opens
    app = qt_window(backend)
    pump(app, until=lambda: app.dialogs.current is not None)
    welcome = app.dialogs.current
    assert isinstance(welcome, WelcomeDialog)
    english, spanish = load_catalog("en"), load_catalog("es")
    assert welcome.languages["es"].text() == spanish.text("gui.welcome.language_es")
    assert welcome.start.text() == english.text("gui.welcome.start")
    welcome.languages["es"].click()
    pump(app, seconds=0.05)
    assert app.dialogs.current is welcome and welcome.isVisible()  # still open, now in Spanish
    assert welcome.start.text() == spanish.text("gui.welcome.start")
    assert welcome.windowTitle() == spanish.text("gui.welcome.title")
    assert backend.settings.language == "es"
    welcome.close_dialog()


def test_ac_04_results_say_how_to_use_it(qt_window: Window, tmp_path: Path) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    app.presenter.choose_tool(Tool.CONVERT)
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=lambda: converted(app) and app.presenter.page == 4, seconds=10)
    result = app.shown.last_result
    assert result is not None and result.with_ai
    line = app.results.with_ai
    assert line.isVisible() and line.text() == result.with_ai and line.wordWrap()
