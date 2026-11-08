"""Feature 023 — the start screen and Split's step 1 on the three windows (AC-08, AC-09, AC-10):
each window opened on the presenter's fake backend, its tiles pressed as a user would."""

from collections.abc import Callable, Iterator

import pytest
from support.flet_acceptance import QUIET, click, windows
from support.gui_fakes import MemoryBackend

from clearmd.frontend.flet import FletApp
from clearmd.frontend.presenter.state import HOME, Tool
from clearmd.frontend.pyside import PySideApp
from clearmd.frontend.ttk import TtkApp


@pytest.fixture
def flet_window() -> Iterator[Callable[..., FletApp]]:
    yield from windows()


def test_ac_08_the_three_windows_open_on_the_start_screen_and_a_tile_opens_its_tool(
    window: Callable[..., TtkApp],
    qt_window: Callable[..., PySideApp],
    flet_window: Callable[..., FletApp],
) -> None:
    ttk = window(MemoryBackend(QUIET))
    assert ttk.presenter.page == HOME and set(ttk.home.tiles) == {
        Tool.CONVERT,
        Tool.SPLIT,
        Tool.MERGE,
    }  # 026
    ttk.home.tiles[Tool.SPLIT].choose()
    assert (ttk.presenter.page, ttk.presenter.tool) == (1, Tool.SPLIT)
    ttk.presenter.go_to(HOME)
    assert ttk.presenter.page == HOME

    qt = qt_window(MemoryBackend(QUIET))
    assert qt.presenter.page == HOME and len(qt.home.tiles) == 3
    qt.home.split.button.click()
    assert (qt.presenter.page, qt.presenter.tool) == (1, Tool.SPLIT)
    qt.home.convert.button.click()  # from Home again: the other tool
    assert qt.presenter.tool is Tool.CONVERT

    flet = flet_window(MemoryBackend(QUIET))
    assert flet.presenter.page == HOME and len(flet.home.tiles) == 3
    click(flet.home.split.control)
    assert (flet.presenter.page, flet.presenter.tool) == (1, Tool.SPLIT)


def test_ac_09_split_names_its_steps_and_asks_how_to_cut_and_what_to_keep(
    window: Callable[..., TtkApp],
    qt_window: Callable[..., PySideApp],
    flet_window: Callable[..., FletApp],
) -> None:
    for open_window in (window, qt_window, flet_window):
        backend = MemoryBackend(QUIET)
        app = open_window(backend)
        app.presenter.choose_tool(Tool.SPLIT)
        catalog = app.presenter.catalog
        assert catalog.text("gui.page.choose_title") == "Choose What to Split"
        assert catalog.text("gui.steps.convert") == "Split"
        app.presenter.choose_split(cut="pages", pages=20, keep="pdf")
        settings = backend.settings
        assert (settings.split_cut, settings.split_pages, settings.split_keep) == (
            "pages",
            20,
            "pdf",
        )


def test_ac_10_the_split_choices_come_back_in_a_new_window(
    window: Callable[..., TtkApp], qt_window: Callable[..., PySideApp]
) -> None:
    backend = MemoryBackend(QUIET)
    first = window(backend)
    first.presenter.choose_tool(Tool.SPLIT)
    first.presenter.choose_split(cut="pages", pages=12, keep="markdown")
    again = qt_window(backend)  # another window, the same settings file
    assert again.presenter.settings.split_pages == 12
    assert again.presenter.settings.split_keep == "markdown"
