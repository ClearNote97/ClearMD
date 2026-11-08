"""Feature 033 in the flet window: Results' "What Next?" as the three tools in small tiles (the one
just used first, with the accent border), one box for the files ticked every time, and Cancel."""

from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import flet as ft
import pytest
from support.flet_acceptance import QUIET, Window, click, page_of, windows
from support.gui_fakes import FakeBackend

from clearmd.frontend.design.metrics import GAP
from clearmd.frontend.design.tool_art import svg
from clearmd.frontend.flet import FletApp
from clearmd.frontend.flet.components.tool_icon import INK
from clearmd.frontend.flet.views.dialogs.what_next import ICON, WhatNextDialog
from clearmd.frontend.flet.visuals.look import tile_style
from clearmd.frontend.presenter.state import Tool
from clearmd.i18n import load_catalog


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def opened(flet_window: Window, tool: Tool = Tool.CONVERT, language: str = "en") -> FletApp:
    app = flet_window(FakeBackend(settings=replace(QUIET, language=language)))
    app.presenter.choose_tool(tool)
    app.presenter.add_paths([Path("/d/a.pdf")])
    return app


def what_next(app: FletApp) -> WhatNextDialog:
    app.dialogs.what_next()  # as Results' "What Next?" opens it
    dialog = app.dialogs.current
    assert isinstance(dialog, WhatNextDialog)
    return dialog


@pytest.mark.parametrize("language", ["en", "es"])
def test_the_tiles_the_box_and_cancel(flet_window: Window, language: str) -> None:
    app = opened(flet_window, language=language)
    catalog = load_catalog(language)
    dialog = what_next(app)
    assert dialog.title.value == catalog.text("gui.more.title")
    assert list(dialog.tiles) == [Tool.CONVERT, Tool.SPLIT, Tool.MERGE]
    titles = [choice.title for choice in app.presenter.next_choices()]
    for tile, title in zip(dialog.tiles.values(), titles, strict=True):
        column = tile.content
        assert isinstance(column, ft.Column)
        icon, text = column.controls
        assert isinstance(icon, ft.Image) and isinstance(text, ft.Text) and text.value == title
    assert dialog.keep.label == catalog.text("gui.more.keep") and dialog.keep.value is True
    assert dialog.keep_help.value == catalog.text("gui.more.keep_help")
    assert dialog.cancel.content == catalog.text("gui.more.cancel")
    assert dialog.foot.controls[-1] is dialog.cancel


@pytest.mark.parametrize("used", list(Tool))
def test_the_tool_just_used_comes_first_with_the_accent(flet_window: Window, used: Tool) -> None:
    app = opened(flet_window, used)
    dialog = what_next(app)
    tools = list(dialog.tiles)
    assert tools[0] is used and sorted(tools) == sorted(Tool)
    for tool, tile in dialog.tiles.items():
        assert tile.style == tile_style(GAP, current=tool is used)
    column = dialog.tiles[used].content
    assert isinstance(column, ft.Column)
    icon = column.controls[0]
    assert (
        isinstance(icon, ft.Image) and icon.src == svg(used, INK, ICON).encode()
    )  # the start screen's icon, smaller


@pytest.mark.parametrize("keep", [True, False])
@pytest.mark.parametrize("tool", list(Tool))
def test_one_click_opens_the_tool_with_or_without_the_files(
    flet_window: Window, tool: Tool, keep: bool
) -> None:
    app = opened(flet_window)
    dialog = what_next(app)
    refreshes = page_of(app).refreshes
    dialog.keep.value = keep
    click(dialog.tiles[tool])
    assert app.dialogs.current is None and page_of(app).refreshes > refreshes  # sent at once
    assert (app.presenter.page, app.presenter.tool) == (1, tool)
    assert bool(app.main.inputs.rows()) is keep


def test_the_box_is_ticked_every_time(flet_window: Window) -> None:
    app = opened(flet_window)
    dialog = what_next(app)
    dialog.keep.value = False
    dialog.close_dialog()
    assert what_next(app).keep.value is True


def test_cancel_and_escape_only_close(flet_window: Window) -> None:
    app = opened(flet_window)
    page_before, tool_before = app.presenter.page, app.presenter.tool
    click(what_next(app).cancel)
    assert app.dialogs.current is None
    what_next(app)
    page_of(app).press("Escape")
    assert app.dialogs.current is None
    assert (app.presenter.page, app.presenter.tool) == (page_before, tool_before)
    assert [row.name for row in app.main.inputs.rows()] == ["a.pdf"]
