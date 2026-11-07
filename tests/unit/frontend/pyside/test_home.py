"""Feature 023 in the Qt window: it opens on the start screen, a tile opens step 1 of its tool, and
Home in the rail brings the start screen back while no work is running (AC-08)."""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Qt
from support.gui_fakes import FakeBackend
from support.pyside_acceptance import QUIET, drop, press, pump

from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.state import HOME, Tool
from clearmd.frontend.pyside import PySideApp

Window = Callable[..., PySideApp]


def test_the_window_opens_on_the_start_screen_with_its_two_tiles(window: Window) -> None:
    app = window()
    assert app.presenter.page == HOME
    assert app.home.isVisible() and not app.main.isVisible()
    assert app.home.convert.title.text() == "Convert to Markdown"
    assert app.home.split.title.text() == "Split a PDF"
    assert app.home.convert.body.text() and app.home.split.body.text()
    assert app.home.note.text() == "The tools change files, never what is inside them."
    assert not app.home.convert.icon.pixmap().isNull()
    assert not app.home.split.icon.pixmap().isNull()
    assert app.surface.title.text() == "What Do You Want to Do?"
    assert app.surface.eyebrow.isHidden()  # no "Step N of 4" on the start screen
    assert app.actions.isHidden()  # nor a primary action
    assert app.rail.home.property("current") == "true"
    assert all(not text.startswith("> ") for text in app.rail.step_texts())
    assert app.home.convert.button.hasFocus()  # the keyboard starts on the first tile


def test_the_convert_tile_opens_step_1_of_convert(window: Window) -> None:
    app = window()
    app.home.convert.button.click()
    assert app.presenter.page == 1 and app.presenter.tool is Tool.CONVERT
    assert app.main.isVisible() and not app.home.isVisible()
    assert app.surface.title.text() == "Choose What to Convert"
    assert not app.surface.eyebrow.isHidden() and not app.actions.isHidden()
    assert app.rail.step_texts()[0].startswith("> ")
    assert app.rail.home.property("current") == "false"


def test_the_split_tile_opens_step_1_of_split_in_its_words(window: Window) -> None:
    app = window()
    app.home.split.button.click()
    assert app.presenter.page == 1 and app.presenter.tool is Tool.SPLIT
    assert app.surface.title.text() == "Choose What to Split"
    assert app.rail.step_texts()[2] == "Split"


def test_enter_on_a_focused_tile_opens_it(window: Window) -> None:
    app = window()
    app.home.split.button.setFocus()
    pump(app, seconds=0.05)
    press(app, Qt.Key.Key_Return)
    assert app.presenter.page == 1 and app.presenter.tool is Tool.SPLIT
    assert app.main.add_files.hasFocus()  # the keyboard where step 1 starts


def test_home_in_the_rail_brings_the_start_screen_back(window: Window) -> None:
    app = window()
    app.home.convert.button.click()
    app.rail.home.click()
    assert app.presenter.page == HOME
    assert app.home.isVisible() and app.actions.isHidden()
    assert app.surface.title.text() == "What Do You Want to Do?"


def test_home_in_the_rail_is_shut_while_working(window: Window) -> None:
    app = window()
    shown = app.shown.state
    assert shown is not None and app.rail.home.isEnabled()
    for state in (AppState.ANALYZING, AppState.CONVERTING):
        app.view.show_state(replace(shown, state=state))
        assert not app.rail.home.isEnabled()
    app.view.show_state(shown)
    assert app.rail.home.isEnabled()


def test_the_start_screen_speaks_spanish(window: Window) -> None:
    app = window(FakeBackend(settings=replace(QUIET, language="es")))
    assert app.home.split.title.text() == "Dividir un PDF"
    assert app.surface.title.text() == "¿Qué Quieres Hacer?"
    assert app.rail.home.accessibleName() == "Inicio"


def test_files_dropped_on_the_start_screen_open_step_1_with_them(
    window: Window, tmp_path: Path
) -> None:
    app = window()
    document = tmp_path / "a.pdf"
    document.write_bytes(b"")
    drop(app, document)
    pump(app, seconds=0.05)
    assert app.presenter.page == 1 and app.main.isVisible() and not app.home.isVisible()
    assert app.main.inputs.tree.topLevelItemCount() == 1
    assert not app.actions.isHidden()
