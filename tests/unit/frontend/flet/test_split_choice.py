"""Feature 023 in the flet window: How to Split on step 1 of Split, in place of the images' choice,
each control a call to the presenter; and the settings' Split a PDF group, saved with Save."""

from collections.abc import Iterator
from dataclasses import replace

import flet as ft
import pytest
from support.flet_acceptance import QUIET, Window, click, texts, windows
from support.gui_fakes import FakeBackend

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.flet import FletApp
from clearmd.frontend.flet.views.dialogs.settings import SettingsDialog
from clearmd.frontend.presenter.state import Tool
from clearmd.i18n import load_catalog


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def split_window(flet_window: Window, settings: Settings = QUIET) -> tuple[FletApp, FakeBackend]:
    backend = FakeBackend(settings=settings)
    app = flet_window(backend)
    click(app.home.split.control)
    return app, backend


def test_how_to_split_shows_only_for_split_in_place_of_the_images(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    click(app.home.convert.control)
    assert not app.main.split.control.visible and app.main.images.control.visible
    app.presenter.go_to(0)
    click(app.home.split.control)
    assert app.main.split.control.visible and not app.main.images.control.visible
    assert app.main.summary.control.visible and app.main.mode.control.visible  # they stay
    catalog = load_catalog("en")
    shown = texts(app.main.split.control)
    for key in ("gui.split.title", "gui.split.parts", "gui.split.pages", "gui.split.keep"):
        assert catalog.text(key) in shown
    assert catalog.text("gui.split.note") in shown
    split = app.main.split
    assert split.cut.radios["parts"].label == catalog.text("gui.split.into")
    assert split.keep.radios["both"].label == catalog.text("gui.split.keep_both")


def test_the_block_shows_the_stored_choice(flet_window: Window) -> None:
    settings = replace(QUIET, split_cut="pages", split_parts=7, split_pages=30, split_keep="pdf")
    app, _backend = split_window(flet_window, settings)
    split = app.main.split
    assert split.cut.value == "pages" and split.keep.value == "pdf"
    assert split.parts.field.value == "7" and split.pages.field.value == "30"


def test_each_control_calls_choose_split(flet_window: Window) -> None:
    app, backend = split_window(flet_window)
    split = app.main.split
    split.cut.choose("pages")
    assert backend.settings.split_cut == "pages"
    split.keep.choose("markdown")
    assert backend.settings.split_keep == "markdown"
    split.parts.type("12")
    assert backend.settings.split_parts == 2  # nothing on a keystroke
    assert split.parts.field.on_submit is not None
    split.parts.field.on_submit()  # type: ignore[call-arg]  # Enter
    assert backend.settings.split_parts == 12
    split.pages.type("25")
    assert split.pages.field.on_blur is not None
    split.pages.field.on_blur()  # type: ignore[call-arg]  # the focus leaves it
    assert backend.settings.split_pages == 25


@pytest.mark.parametrize("typed", ["1", "0", "20000", ""])
def test_a_refused_number_is_put_back(flet_window: Window, typed: str) -> None:
    app, backend = split_window(flet_window)
    parts = app.main.split.parts
    parts.type(typed)
    parts.commit()
    assert backend.settings.split_parts == 2 and parts.field.value == "2"


def test_the_block_is_disabled_with_the_other_choices(flet_window: Window) -> None:
    app, _backend = split_window(flet_window)
    split = app.main.split
    assert not split.parts.field.disabled and not split.cut.radios["pages"].disabled
    split.set_disabled(True)
    assert split.parts.field.disabled and split.keep.radios["pdf"].disabled


def open_settings(app: FletApp) -> SettingsDialog:
    click(app.rail.settings)
    dialog = app.dialogs.current
    assert isinstance(dialog, SettingsDialog)
    return dialog


def test_the_settings_group_round_trips(flet_window: Window) -> None:
    app, backend = split_window(flet_window)
    dialog = open_settings(app)
    group = dialog.split
    assert group.cut.value == "parts" and group.keep.value == "both"
    assert group.parts.value == "2" and group.pages.value == "50"
    catalog = load_catalog("en")
    assert catalog.text("gui.settings.split") in texts(dialog.body)
    assert isinstance(group.keep, ft.Dropdown)
    assert [option.text for option in group.keep.options or []] == [
        catalog.text(f"gui.split.keep_{value}") for value in ("pdf", "markdown", "both")
    ]
    group.cut.value, group.pages.value, group.keep.value = "pages", "40", "pdf"
    group.parts.value = "1"  # out of its range: the saved one is kept
    dialog.save()
    saved = backend.settings
    assert (saved.split_cut, saved.split_parts, saved.split_pages, saved.split_keep) == (
        "pages", 2, 40, "pdf"
    )  # fmt: skip
    assert app.main.split.cut.value == "pages" and app.main.split.pages.field.value == "40"
    dialog = open_settings(app)
    assert dialog.split.pages.value == "40"  # loaded again from the saved settings
    dialog.restore()
    assert dialog.split.cut.value == "parts" and dialog.split.pages.value == "50"
    assert app.presenter.tool is Tool.SPLIT
