"""Feature 033 on the flet window (spec/features/033_*/spec.md, AC-04): Results' "What Next?" as
in the other two windows: the three tools' tiles in one row (the one just used first, "<tool>
Again"), the box for the files under them, Cancel at the foot. The window runs on a page that is
not flet's, on the presenter's fake backend."""

from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import flet as ft
import pytest
from support.flet_acceptance import QUIET, Window, click, confirm, converted, pump, windows
from support.gui_fakes import FakeBackend

from clearmd.frontend.flet import FletApp
from clearmd.frontend.flet.views.dialogs.what_next import WhatNextDialog
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.state import Tool
from clearmd.i18n import load_catalog


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def to_results(app: FletApp, tool: Tool, folder: Path) -> WhatNextDialog:
    click({Tool.CONVERT: app.home.convert, Tool.SPLIT: app.home.split,
           Tool.MERGE: app.home.merge}[tool].control)  # fmt: skip
    app.presenter.add_paths([folder])
    click(app.actions.primary)
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION, seconds=30)
    confirm(app)
    pump(app, until=lambda: converted(app) and app.presenter.page == 4, seconds=30)
    assert app.actions.secondary.visible
    click(app.actions.secondary)  # "What Next?"
    dialog = app.dialogs.current
    assert isinstance(dialog, WhatNextDialog)
    return dialog


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_04_the_tiles_in_a_row_the_box_under_them_cancel_at_the_foot(
    flet_window: Window, tmp_path: Path, language: str
) -> None:
    app = flet_window(FakeBackend(settings=replace(QUIET, language=language)))
    dialog = to_results(app, Tool.CONVERT, tmp_path)
    catalog = load_catalog(language)
    body = dialog.body.controls
    row = body[0]
    assert isinstance(row, ft.Row) and row.controls == list(dialog.tiles.values())  # one row
    assert body.index(dialog.keep) > 0  # the box under the tiles, its help just below
    first = dialog.tiles[Tool.CONVERT].content
    assert isinstance(first, ft.Column)
    again = catalog.text("gui.more.again", tool=catalog.text("gui.more.convert"))
    assert [c.value for c in first.controls if isinstance(c, ft.Text)] == [again]
    assert dialog.foot.controls[-1] is dialog.cancel  # Cancel at the foot
    assert dialog.cancel.content == catalog.text("gui.more.cancel")


def test_ac_04_a_tile_opens_its_tool_and_the_box_decides_the_files(
    flet_window: Window, tmp_path: Path
) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    dialog = to_results(app, Tool.CONVERT, tmp_path)
    assert list(dialog.tiles) == [Tool.CONVERT, Tool.SPLIT, Tool.MERGE]
    dialog.keep.value = False  # start empty
    click(dialog.tiles[Tool.SPLIT])
    assert app.dialogs.current is None
    assert (app.presenter.page, app.presenter.tool) == (1, Tool.SPLIT)
    assert app.main.inputs.rows() == () and app.main.start.control.visible


def test_ac_04_cancel_leaves_results_as_they_are(flet_window: Window, tmp_path: Path) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    dialog = to_results(app, Tool.CONVERT, tmp_path)
    click(dialog.cancel)
    assert app.dialogs.current is None and app.presenter.page == 4
    assert app.presenter.state in {AppState.FINISHED, AppState.FINISHED_WITH_PROBLEMS}
