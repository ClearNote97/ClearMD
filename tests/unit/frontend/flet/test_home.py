"""Feature 023 in the flet window: it opens on Home, the start screen, with the two tools' tiles;
each tile opens step 1 of its tool; Home on the rail (and Ctrl+0) brings it back while no work
runs. The window is driven on a page that is not flet's, on the presenter's fake backend."""

from collections.abc import Iterator
from dataclasses import replace

import flet as ft
import pytest
from support.flet_acceptance import QUIET, Window, click, page_of, windows
from support.gui_fakes import FakeBackend

from clearmd.frontend.design.tool_art import svg
from clearmd.frontend.flet import FletApp
from clearmd.frontend.flet.components.tool_icon import INK
from clearmd.frontend.flet.views.home import HOME_ICON_SIZE
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.state import HOME, Tool
from clearmd.i18n import load_catalog


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def on_home(app: FletApp) -> bool:
    return bool(app.home.control.visible) and not any(page.visible for page in app.pages)


@pytest.mark.parametrize("language", ["en", "es"])
def test_the_window_opens_on_home_with_the_two_tiles(flet_window: Window, language: str) -> None:
    app = flet_window(FakeBackend(settings=replace(QUIET, language=language)))
    catalog = load_catalog(language)
    assert app.presenter.page == HOME and on_home(app)
    for tile, name in ((app.home.convert, "convert"), (app.home.split, "split")):
        assert isinstance(tile.icon, ft.Image)  # the app's own picture (032)
        assert tile.icon.src == svg(name, INK, HOME_ICON_SIZE).encode()
        assert tile.title.value == catalog.text(f"gui.home.{name}")
        assert tile.body.value == catalog.text(f"gui.home.{name}_body")
        assert isinstance(tile.control, ft.Button) and not tile.control.disabled
    assert app.home.note.value == catalog.text("gui.home.files_note")
    assert app.surface.title.value == catalog.text("gui.home.title")
    assert app.surface.subtitle.value == catalog.text("gui.home.subtitle")
    assert not app.surface.eyebrow.visible  # no "Step N of 4" on Home
    assert not app.actions.control.visible  # no primary action on Home
    assert app.rail.home_text() == "> " + catalog.text("gui.home.step")
    assert app.rail.home.tooltip == catalog.text("gui.home.step")


def test_the_convert_tile_opens_step_1_of_convert(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    click(app.home.convert.control)
    assert app.presenter.page == 1 and app.presenter.tool is Tool.CONVERT
    assert app.pages[0].visible and not app.home.control.visible
    assert app.actions.control.visible and app.surface.eyebrow.visible
    assert app.surface.title.value == load_catalog("en").text("gui.page.choose_title")
    assert app.rail.step_texts()[0] == "> Choose" and not app.rail.home_text().startswith(">")


def test_the_split_tile_opens_step_1_of_split_with_its_words(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    click(app.home.split.control)
    split = load_catalog("en").for_tool(Tool.SPLIT)
    assert app.presenter.page == 1 and app.presenter.tool is Tool.SPLIT
    assert app.pages[0].visible and not app.home.control.visible
    assert app.surface.title.value == split.text("gui.page.choose_title") == "Choose What to Split"
    assert app.rail.step_texts()[2] == split.text("gui.steps.convert") == "Split"
    assert app.home.split.title.value == split.text("gui.home.split")  # Home keeps its words


def test_home_on_the_rail_and_ctrl_0_bring_it_back(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    click(app.home.convert.control)
    click(app.rail.home)
    assert app.presenter.page == HOME and on_home(app)
    click(app.rail.steps[1])
    page_of(app).press("0", ctrl=True)
    assert app.presenter.page == HOME and on_home(app)


def test_home_is_disabled_on_the_rail_while_working(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    click(app.home.convert.control)
    state = app.shown.state
    assert state is not None and not app.rail.home.disabled
    app.view.show_state(replace(state, state=AppState.CONVERTING, page=3))
    assert app.rail.home.disabled
    app.view.show_state(state)
    assert not app.rail.home.disabled
