"""Feature 026 in the flet window: Home's third tile, Merge Documents; How to Merge on step 1 of
Merge, in place of the images and of Split's block, each radio a call to the presenter; and the
settings' Merge choice, saved with Save."""

from collections.abc import Iterator
from dataclasses import replace

import flet as ft
import pytest
from support.flet_acceptance import QUIET, Window, click, texts, windows
from support.gui_fakes import FakeBackend

from clearmd.frontend.flet import FletApp
from clearmd.frontend.flet.views.dialogs.settings import SettingsDialog
from clearmd.frontend.presenter.state import Tool
from clearmd.i18n import load_catalog


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def merge_window(flet_window: Window, language: str = "en") -> tuple[FletApp, FakeBackend]:
    backend = FakeBackend(settings=replace(QUIET, language=language))
    app = flet_window(backend)
    click(app.home.merge.control)
    return app, backend


@pytest.mark.parametrize("language", ["en", "es"])
def test_home_has_three_tiles_of_equal_width(flet_window: Window, language: str) -> None:
    app = flet_window(FakeBackend(settings=replace(QUIET, language=language)))
    catalog = load_catalog(language)
    assert app.home.tiles == (app.home.convert, app.home.split, app.home.merge)
    merge = app.home.merge
    assert merge.icon.icon == ft.Icons.MERGE
    assert merge.title.value == catalog.text("gui.home.merge")
    assert merge.body.value == catalog.text("gui.home.merge_body")
    assert {tile.control.expand for tile in app.home.tiles} == {True}  # one row, equal shares
    assert {tile.control.height for tile in app.home.tiles} == {app.home.convert.control.height}


@pytest.mark.parametrize("language", ["en", "es"])
def test_the_merge_tile_opens_step_1_of_merge(flet_window: Window, language: str) -> None:
    app, _backend = merge_window(flet_window, language)
    words = load_catalog(language).for_tool(Tool.MERGE)
    assert app.presenter.page == 1 and app.presenter.tool is Tool.MERGE
    assert app.pages[0].visible and not app.home.control.visible
    assert app.surface.title.value == words.text("gui.page.choose_title")
    assert app.rail.step_texts()[2] == words.text("gui.steps.convert")


def test_how_to_merge_shows_only_for_merge(flet_window: Window) -> None:
    app, _backend = merge_window(flet_window)
    main = app.main
    assert main.merge.control.visible
    assert not main.split.control.visible and not main.images.control.visible
    assert main.summary.control.visible and main.mode.control.visible  # they stay
    catalog = load_catalog("en")
    shown = texts(main.merge.control)
    for key in ("gui.merge.title", "gui.merge.into", "gui.merge.note"):
        assert catalog.text(key) in shown
    assert main.merge.into.radios["pdf"].label == catalog.text("gui.merge.pdf")
    for tool in (Tool.CONVERT, Tool.SPLIT):
        app.presenter.go_to(0)
        app.presenter.choose_tool(tool)
        assert not main.merge.control.visible
    assert main.split.control.visible


def test_each_radio_calls_the_presenter_and_shows_its_choice(flet_window: Window) -> None:
    app, backend = merge_window(flet_window)
    into = app.main.merge.into
    assert into.value == "markdown"
    into.choose("pdf")
    assert backend.settings.merge_into == "pdf" and into.value == "pdf"
    into.choose("markdown")
    assert backend.settings.merge_into == "markdown"


def test_the_block_is_disabled_with_the_other_choices(flet_window: Window) -> None:
    app, _backend = merge_window(flet_window)
    into = app.main.merge.into
    assert not into.radios["pdf"].disabled
    app.main.merge.set_disabled(True)
    assert into.radios["pdf"].disabled and into.radios["markdown"].disabled


def test_the_settings_choice_round_trips(flet_window: Window) -> None:
    app, backend = merge_window(flet_window)
    click(app.rail.settings)
    dialog = app.dialogs.current
    assert isinstance(dialog, SettingsDialog)
    control = dialog.controls["merge_into"]
    assert isinstance(control, ft.Dropdown) and control.value == "markdown"
    catalog = load_catalog("en")
    assert [option.text for option in control.options or []] == [
        catalog.text("gui.merge.markdown"),
        catalog.text("gui.merge.pdf"),
    ]
    assert catalog.text("gui.settings.merge") in texts(dialog.body)
    control.value = "pdf"
    dialog.save()
    assert backend.settings.merge_into == "pdf" and app.main.merge.into.value == "pdf"
    click(app.rail.settings)
    dialog = app.dialogs.current
    assert isinstance(dialog, SettingsDialog)
    assert dialog.controls["merge_into"].value == "pdf"
    dialog.restore()
    assert dialog.controls["merge_into"].value == "markdown"
