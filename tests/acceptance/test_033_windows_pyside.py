"""Feature 033 in the PySide6 window (spec/features/033_*/spec.md): "What Next?" as three small
tiles in a row with the start screen's icons, the box under them, Cancel at the foot (AC-04)."""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QWidget
from support.gui_fakes import FakeBackend
from support.pyside_acceptance import QUIET, confirm, converted, pump, to_review

from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.pyside import PySideApp
from clearmd.frontend.pyside.components.tile import SMALL_ICON
from clearmd.frontend.pyside.components.tile_art import tool_art
from clearmd.frontend.pyside.views.dialogs.what_next import WhatNextDialog

Window = Callable[..., PySideApp]
SMOOTH = Qt.TransformationMode.SmoothTransformation


def open_what_next(app: PySideApp, folder: Path, tool: Tool = Tool.CONVERT) -> WhatNextDialog:
    app.presenter.choose_tool(tool)
    to_review(app, folder)
    confirm(app)
    pump(app, until=lambda: converted(app) and app.presenter.page == 4, seconds=10)
    app.actions.secondary.click()
    pump(app, seconds=0.1)
    dialog = app.dialogs.current
    assert isinstance(dialog, WhatNextDialog)
    return dialog


def top_left(widget: QWidget, dialog: WhatNextDialog) -> QPoint:
    return widget.mapTo(dialog, QPoint(0, 0))


def test_ac_04_three_tiles_in_a_row_the_box_under_them_cancel_at_the_foot(
    qt_window: Window, tmp_path: Path
) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    dialog = open_what_next(app, tmp_path)
    assert dialog.windowTitle() == "What Next?"
    titles = [tile.title.text() for tile in dialog.tiles]
    assert titles == ["Convert Again", "Split", "Merge"]
    tops = {top_left(tile.button, dialog).y() for tile in dialog.tiles}
    assert len(tops) == 1  # one row
    xs = [top_left(tile.button, dialog).x() for tile in dialog.tiles]
    assert xs == sorted(xs)
    under = top_left(dialog.tiles[0].button, dialog).y() + dialog.tiles[0].button.height()
    assert top_left(dialog.keep, dialog).y() > under  # the box under the tiles
    assert dialog.keep.text() == "Keep the files you chose" and dialog.keep.isChecked()
    assert top_left(dialog.cancel, dialog).y() > top_left(dialog.keep, dialog).y()
    assert dialog.cancel.text() == "Cancel"
    current = [tile.button.property("current") for tile in dialog.tiles]
    assert current == ["true", "false", "false"]  # the tool just used, in the accent
    colour = app.shown.palette.accent_text
    for tool, tile in zip(Tool, dialog.tiles, strict=True):  # the start screen's icons
        shown = tile.icon.pixmap().toImage()
        drawn = tool_art(tool, SMALL_ICON, colour).toImage()
        if drawn.size() != shown.size():  # the label keeps the screen's own density
            drawn = drawn.scaled(
                shown.size(), Qt.AspectRatioMode.IgnoreAspectRatio, SMOOTH
            ).convertToFormat(shown.format())
        assert shown == drawn, tool
    dialog.cancel.click()


@pytest.mark.parametrize("keep", [True, False])
def test_ac_04_a_tile_opens_its_tool_with_the_box(
    qt_window: Window, tmp_path: Path, keep: bool
) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    dialog = open_what_next(app, tmp_path, Tool.SPLIT)
    assert [tile.title.text() for tile in dialog.tiles] == ["Split Again", "Convert", "Merge"]
    dialog.keep.setChecked(keep)
    dialog.tiles[2].button.click()  # Merge
    assert app.dialogs.current is None
    assert (app.presenter.page, app.presenter.tool) == (1, Tool.MERGE)
    assert bool(app.main.inputs.rows()) is keep


def test_ac_04_cancel_and_esc_only_close_it_and_the_box_is_ticked_again(
    qt_window: Window, tmp_path: Path
) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    dialog = open_what_next(app, tmp_path)
    dialog.keep.setChecked(False)
    dialog.cancel.click()
    assert app.dialogs.current is None and app.presenter.page == 4
    app.actions.secondary.click()
    again = app.dialogs.current
    assert isinstance(again, WhatNextDialog) and again.keep.isChecked()
    QTest.keyClick(again, Qt.Key.Key_Escape)
    pump(app, seconds=0.05)
    assert app.dialogs.current is None and app.presenter.page == 4
    assert app.presenter.tool is Tool.CONVERT


def test_ac_04_it_speaks_spanish(qt_window: Window, tmp_path: Path) -> None:
    app = qt_window(FakeBackend(settings=replace(QUIET, language="es")))
    dialog = open_what_next(app, tmp_path)
    assert dialog.windowTitle() == "¿Qué Sigue?" and dialog.cancel.text()
    assert dialog.tiles[0].title.text().startswith("Convertir")
    dialog.cancel.click()
