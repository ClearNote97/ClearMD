"""Feature 032 on the flet window (spec/features/032_*/spec.md, AC-04 and AC-05): Home's three
tiles centred with the app's own icons; Merge's order buttons; Results' "What Next?" going back
Home; no button taken by the focus when a page opens. The window runs on a page that is not
flet's, on the presenter's fake backend."""

from collections.abc import Iterator
from pathlib import Path

import flet as ft
import pytest
from support.flet_acceptance import QUIET, Window, click, confirm, converted, pump, walk, windows
from support.gui_fakes import FakeBackend

from clearmd.frontend.design.tool_art import svg
from clearmd.frontend.flet import FletApp
from clearmd.frontend.flet.components.tool_icon import INK
from clearmd.frontend.flet.views.dialogs.what_next import WhatNextDialog
from clearmd.frontend.flet.views.home import HOME_ICON_SIZE
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.state import HOME, Tool


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def test_ac_04_home_draws_the_apps_own_icons_centred(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    assert app.presenter.page == HOME and app.home.control.visible
    for tile, tool in zip(app.home.tiles, (Tool.CONVERT, Tool.SPLIT, Tool.MERGE), strict=True):
        assert isinstance(tile.icon, ft.Image)
        assert tile.icon.src == svg(tool, INK, HOME_ICON_SIZE).encode()  # tool_art's shapes
        assert not any(isinstance(c, ft.Icon) for c in walk(tile.control))  # no Material icon
    page = app.home.control
    assert page.expand and page.alignment == ft.MainAxisAlignment.CENTER  # centred in the page
    assert page.controls[-1] is app.home.note  # the note just under the tiles


def order(app: FletApp) -> list[str]:
    return [row.name for row in app.main.inputs.rows()]


def buttons(app: FletApp, index: int) -> list[ft.IconButton]:
    line = app.main.inputs.lines[index]
    return [c for c in walk(line.frame) if isinstance(c, ft.IconButton)]


def test_ac_05_merge_orders_its_list_with_the_arrows(flet_window: Window, tmp_path: Path) -> None:
    fake = FakeBackend(settings=QUIET)
    app = flet_window(fake)
    click(app.home.merge.control)
    paths = [tmp_path / name for name in ("a.md", "b.md", "c.md")]
    app.presenter.add_paths(paths)
    assert [len(buttons(app, index)) for index in range(3)] == [2, 2, 2]
    first_up, _down = buttons(app, 0)
    _up, last_down = buttons(app, 2)
    assert first_up.disabled and last_down.disabled
    click(buttons(app, 2)[0])  # c.md one place up
    assert order(app) == ["a.md", "c.md", "b.md"]
    click(app.actions.primary)
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION, seconds=30)
    assert fake.plan_calls[-1]["inputs"] == [paths[0], paths[2], paths[1]]  # the merge's order


def test_ac_05_what_next_opens_another_tool_with_the_files(
    flet_window: Window, tmp_path: Path
) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    click(app.home.convert.control)
    app.presenter.add_paths([tmp_path])
    click(app.actions.primary)
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION, seconds=30)
    confirm(app)
    pump(app, until=lambda: converted(app) and app.presenter.page == 4, seconds=30)
    assert app.actions.secondary.visible and app.actions.secondary.content == "What Next?"
    click(app.actions.secondary)
    dialog = app.dialogs.current
    assert isinstance(dialog, WhatNextDialog)  # 032's three answers became 033's tiles
    click(dialog.tiles[Tool.MERGE])  # the box ticked: the files stay
    assert (app.presenter.page, app.presenter.tool) == (1, Tool.MERGE)
    assert order(app) == [f"{tmp_path.name}/"]  # the files are kept


def test_ac_05_no_button_is_taken_when_a_page_opens(flet_window: Window, tmp_path: Path) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    click(app.home.merge.control)
    app.presenter.add_paths([tmp_path / "a.md", tmp_path / "b.md"])
    clear = app.main.clear
    assert callable(clear.on_focus)
    clear.on_focus()  # type: ignore[call-arg]  # Clear All had the focus
    for page in (2, 1, HOME, 4):
        app.presenter.go_to(page)
        assert not app.focus.taken, page  # Enter is the page's again
