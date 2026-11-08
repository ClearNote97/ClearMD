"""Feature 032 in the flet window: Merge's ▲ ▼ on each row of step 1's list and the hint under it;
Results' "What Next?" with Go Back Home; the focus forgotten when a page opens; Summary on the
heading's line for Split and Merge."""

from collections.abc import Callable, Iterator
from dataclasses import replace
from pathlib import Path
from typing import cast

import flet as ft
import pytest
from support.flet_acceptance import QUIET, Window, click, walk, windows
from support.gui_fakes import FakeBackend

from clearmd.frontend.flet import FletApp
from clearmd.frontend.flet.views.dialogs.keep_inputs import KeepInputsDialog
from clearmd.frontend.presenter.state import HOME, Tool
from clearmd.i18n import load_catalog

DOCS = [Path("/d/a.md"), Path("/d/b.md"), Path("/d/c.md")]


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def opened(flet_window: Window, tool: Tool, language: str = "en") -> FletApp:
    app = flet_window(FakeBackend(settings=replace(QUIET, language=language)))
    app.presenter.choose_tool(tool)
    app.presenter.add_paths(DOCS)
    return app


def arrows(app: FletApp) -> list[tuple[ft.IconButton, ft.IconButton]]:
    found = []
    for line in app.main.inputs.lines:
        row = line.frame.content
        assert isinstance(row, ft.Row)
        cell = row.controls[-1]
        assert isinstance(cell, ft.Row)
        up, down = cell.controls
        assert isinstance(up, ft.IconButton) and isinstance(down, ft.IconButton)
        found.append((up, down))
    return found


def names(app: FletApp) -> list[str]:
    return [row.name for row in app.main.inputs.rows()]


@pytest.mark.parametrize("language", ["en", "es"])
def test_merge_rows_have_their_arrows_and_the_hint(flet_window: Window, language: str) -> None:
    app = opened(flet_window, Tool.MERGE, language)
    catalog = load_catalog(language)
    pairs = arrows(app)
    assert [(not up.disabled, not down.disabled) for up, down in pairs] == [
        (False, True),
        (True, True),
        (True, False),
    ]
    first_up, last_down = pairs[0][0], pairs[2][1]  # a disabled arrow looks disabled (CI shot)
    assert first_up.icon_color == last_down.icon_color != pairs[1][0].icon_color
    up, down = pairs[1]
    assert up.tooltip == catalog.text("gui.main.move_up")
    assert down.tooltip == catalog.text("gui.main.move_down")
    hint = app.main._inputs_card.order_hint
    assert hint.visible and hint.value == catalog.text("gui.main.order_hint")


def test_the_arrows_move_a_document(flet_window: Window) -> None:
    app = opened(flet_window, Tool.MERGE)
    click(arrows(app)[2][0])  # c.md up
    assert names(app) == ["a.md", "c.md", "b.md"]
    click(arrows(app)[0][1])  # a.md down
    assert names(app) == ["c.md", "a.md", "b.md"]
    click(arrows(app)[0][0])  # the first cannot go up: disabled, nothing happens
    assert names(app) == ["c.md", "a.md", "b.md"]


@pytest.mark.parametrize("tool", [Tool.CONVERT, Tool.SPLIT])
def test_convert_and_split_have_no_arrows(flet_window: Window, tool: Tool) -> None:
    app = opened(flet_window, tool)
    for line in app.main.inputs.lines:
        assert not [c for c in walk(line.frame) if isinstance(c, ft.IconButton)]
    assert not app.main._inputs_card.order_hint.visible


def test_a_language_change_redraws_the_arrows(flet_window: Window) -> None:
    app = opened(flet_window, Tool.MERGE)
    app.presenter.save_settings(replace(app.presenter.settings, language="es"))
    up, _down = arrows(app)[1]
    assert up.tooltip == load_catalog("es").text("gui.main.move_up")


def what_next(app: FletApp) -> KeepInputsDialog:
    app.dialogs.convert_more()  # as Results' "What Next?" opens it
    dialog = app.dialogs.current
    assert isinstance(dialog, KeepInputsDialog)
    return dialog


@pytest.mark.parametrize("language", ["en", "es"])
def test_what_next_has_three_answers(flet_window: Window, language: str) -> None:
    app = opened(flet_window, Tool.CONVERT, language)
    catalog = load_catalog(language)
    dialog = what_next(app)
    assert dialog.title.value == catalog.text("gui.more.title")
    assert [dialog.home.content, dialog.clear.content, dialog.keep.content] == [
        catalog.text("gui.more.home"),
        catalog.text("gui.more.clear"),
        catalog.text("gui.more.keep"),
    ]
    assert dialog.foot.controls.index(dialog.home) == 0  # on the left, the others on the right


@pytest.mark.parametrize(
    ("answer", "page", "kept"), [("keep", 1, True), ("clear", 1, False), ("home", HOME, True)]
)
def test_each_answer_reaches_the_presenter(
    flet_window: Window, monkeypatch: pytest.MonkeyPatch, answer: str, page: int, kept: bool
) -> None:
    app = opened(flet_window, Tool.CONVERT)
    seen: list[str] = []
    real = app.presenter.what_next

    def spied(given: str) -> None:
        seen.append(given)
        real(given)

    monkeypatch.setattr(app.presenter, "what_next", spied)
    dialog = what_next(app)
    click({"keep": dialog.keep, "clear": dialog.clear, "home": dialog.home}[answer])
    assert seen == [answer] and app.dialogs.current is None
    assert app.presenter.page == page and bool(names(app)) is kept


def test_a_page_change_forgets_the_focus(flet_window: Window) -> None:
    app = opened(flet_window, Tool.CONVERT)
    on_focus = cast(Callable[[], None], app.main.clear.on_focus)
    on_focus()  # "Clear All" has the focus
    assert app.focus.taken
    click(app.rail.steps[1])  # another page: the control left with its page
    assert not app.focus.taken


@pytest.mark.parametrize(("tool", "beside"), [(Tool.CONVERT, False), (Tool.SPLIT, True)])
def test_split_and_merge_put_the_summary_on_the_headings_line(
    flet_window: Window, tool: Tool, beside: bool
) -> None:
    app = opened(flet_window, tool)
    card = app.main._output
    assert (app.main.summary.control in card._beside.controls) is beside
    assert (app.main.summary.control in card._below.controls) is not beside
    app.presenter.go_to(HOME)
    app.presenter.choose_tool(Tool.MERGE)
    assert app.main.summary.control in card._beside.controls and not card._below.visible
