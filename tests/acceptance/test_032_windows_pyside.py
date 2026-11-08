"""Feature 032 in the PySide6 window (spec/features/032_*/spec.md): the start screen's icons from
the shared ``design.tool_art`` and its tiles centred (AC-04); Merge's order buttons, "What Next?"
(its tiles since 033), and no button looking focused when a page opens (AC-05)."""

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QApplication, QPushButton
from support.gui_fakes import FakeBackend
from support.pyside_acceptance import QUIET, confirm, converted, pump, to_review

from clearmd.frontend.presenter.state import HOME, Tool
from clearmd.frontend.pyside import PySideApp
from clearmd.frontend.pyside.components.tile import ICON_SIZE
from clearmd.frontend.pyside.components.tile_art import tool_art
from clearmd.frontend.pyside.views.dialogs.what_next import WhatNextDialog

Window = Callable[..., PySideApp]
SMOOTH = Qt.TransformationMode.SmoothTransformation


def no_button_focused() -> bool:
    return not isinstance(QApplication.focusWidget(), QPushButton)


def test_ac_04_the_tiles_draw_the_shared_icons(qt_window: Window) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    colour = app.shown.palette.accent_text
    tiles = {"convert": app.home.convert, "split": app.home.split, "merge": app.home.merge}
    for tool, tile in tiles.items():
        shown = tile.icon.pixmap().toImage()
        drawn = tool_art(tool, ICON_SIZE, colour).toImage()  # at twice the size
        if drawn.size() != shown.size():  # the label keeps the screen's own density
            drawn = drawn.scaled(
                shown.size(), Qt.AspectRatioMode.IgnoreAspectRatio, SMOOTH
            ).convertToFormat(shown.format())
        assert shown == drawn, tool


def test_ac_04_the_tiles_are_centred_in_the_page(qt_window: Window) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    app.window.resize(1080, 720)
    pump(app, seconds=0.2)
    card = app.home.tiles[0].parentWidget()
    assert card is not None
    first, last = app.home.tiles[0], app.home.tiles[-1]
    left = first.mapTo(card, QPoint(0, 0)).x()
    right = card.width() - (last.mapTo(card, QPoint(0, 0)).x() + last.width())
    assert abs(left - right) <= 1
    top = first.mapTo(card, QPoint(0, 0)).y()
    note = app.home.note
    bottom = card.height() - (note.mapTo(card, QPoint(0, 0)).y() + note.height())
    assert abs(top - bottom) <= 2
    widths = {tile.width() for tile in app.home.tiles}
    assert max(widths) - min(widths) <= 1


def test_ac_05_merge_moves_a_document_with_its_arrows(qt_window: Window, tmp_path: Path) -> None:
    names = ("a.md", "b.md", "c.md")
    for name in names:
        (tmp_path / name).write_text(f"{name}\n", "utf-8")
    app = qt_window(FakeBackend(settings=QUIET))
    app.home.merge.button.click()
    app.presenter.add_paths([tmp_path / name for name in names])
    pump(app, seconds=0.05)
    arrows = app.main.order.arrows
    assert [(row[-1].isEnabled(), row[+1].isEnabled()) for row in arrows] == [
        (False, True),
        (True, True),
        (True, False),
    ]
    assert arrows[0][-1].accessibleName() == "Move Up" and app.main.order_hint.isVisible()
    arrows[2][-1].click()  # c up one place
    pump(app, seconds=0.05)
    assert [row.name for row in app.main.inputs.rows()] == ["a.md", "c.md", "b.md"]
    assert app.main.order.arrows[1][-1].hasFocus()  # the keyboard follows the document
    app.home.convert.button.click()  # Convert offers no order
    app.presenter.go_to(HOME)
    app.home.convert.button.click()
    assert app.presenter.tool is Tool.CONVERT
    assert not app.main.order_hint.isVisible() and app.main.order.arrows == []


def test_ac_05_what_next_opens_another_tool_keeping_the_files(
    qt_window: Window, tmp_path: Path
) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    app.home.convert.button.click()
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=lambda: converted(app) and app.presenter.page == 4, seconds=10)
    assert app.actions.secondary.text() == "What Next?"
    app.actions.secondary.click()
    dialog = app.dialogs.current
    assert isinstance(dialog, WhatNextDialog)  # its three tiles since 033
    dialog.tiles[1].button.click()  # Split, keeping the files
    assert app.dialogs.current is None and app.presenter.page == 1
    assert app.presenter.tool is Tool.SPLIT
    assert [row.name for row in app.main.inputs.rows()] == [f"{tmp_path.name}/"]
    assert no_button_focused()


def test_ac_05_no_button_looks_focused_when_a_page_opens(qt_window: Window, tmp_path: Path) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    assert no_button_focused()
    app.home.split.button.setFocus()
    app.home.split.button.click()
    assert no_button_focused()
    for page in (2, 3, 4, 1, HOME):
        app.rail.steps[0].setFocus()  # a button with the keyboard before the page changes
        app.presenter.go_to(page)
        assert no_button_focused(), page
