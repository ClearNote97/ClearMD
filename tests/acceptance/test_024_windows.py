"""Feature 024 — the third cut on the three windows (AC-05): each window opened on the fake
backend, Split chosen, the words cut set and remembered."""

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


def test_ac_05_the_words_cut_on_the_three_windows_and_in_settings(
    window: Callable[..., TtkApp],
    qt_window: Callable[..., PySideApp],
    flet_window: Callable[..., FletApp],
) -> None:
    openers: tuple[Callable[..., TtkApp | PySideApp | FletApp], ...] = (
        window,
        qt_window,
        flet_window,
    )
    for number, open_window in enumerate(openers, start=1):
        backend = MemoryBackend(QUIET)
        app = open_window(backend)
        app.presenter.choose_tool(Tool.SPLIT)
        app.presenter.choose_split(cut="words", words=20_000 + number)
        assert (backend.settings.split_cut, backend.settings.split_words) == (
            "words",
            20_000 + number,
        )
        app.presenter.choose_split(words=100)  # under 500: refused, the stored number stays
        assert backend.settings.split_words == 20_000 + number
