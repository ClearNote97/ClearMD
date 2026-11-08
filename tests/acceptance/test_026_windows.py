"""Feature 026 — Merge on the three windows (AC-05): the third tile, Merge's words, and its
choice remembered."""

from collections.abc import Callable, Iterator

import pytest
from support.flet_acceptance import QUIET, windows
from support.gui_fakes import MemoryBackend

from clearmd.frontend.flet import FletApp
from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.pyside import PySideApp
from clearmd.frontend.ttk import TtkApp


@pytest.fixture
def flet_window() -> Iterator[Callable[..., FletApp]]:
    yield from windows()


def test_ac_05_merge_on_the_three_windows(
    window: Callable[..., TtkApp],
    qt_window: Callable[..., PySideApp],
    flet_window: Callable[..., FletApp],
) -> None:
    openers: tuple[Callable[..., TtkApp | PySideApp | FletApp], ...] = (
        window,
        qt_window,
        flet_window,
    )
    for open_window in openers:
        backend = MemoryBackend(QUIET)
        app = open_window(backend)
        app.presenter.choose_tool(Tool.MERGE)
        assert (app.presenter.page, app.presenter.tool) == (1, Tool.MERGE)
        assert app.presenter.catalog.text("gui.page.choose_title") == "Choose What to Merge"
        app.presenter.choose_split(into="pdf")
        assert backend.settings.merge_into == "pdf"
        app.presenter.choose_split(into="zip")  # not a choice: refused
        assert backend.settings.merge_into == "pdf"
