"""The PySide6 window for the unit tests (feature 023): offscreen, on the presenter's fake
backend, closed at the end. Importing the acceptance helpers first sets the offscreen platform."""

from collections.abc import Callable, Iterator
from typing import Any

import pytest
from support.gui_fakes import FakeBackend
from support.pyside_acceptance import QUIET, open_window, shut

from clearmd.frontend.pyside import PySideApp


@pytest.fixture
def window() -> Iterator[Callable[..., PySideApp]]:
    """Opens windows on a ``FakeBackend`` (or the one given) and closes every one at the end."""
    opened: list[PySideApp] = []

    def make(backend: Any = None) -> PySideApp:
        app = open_window(backend if backend is not None else FakeBackend(settings=QUIET))
        opened.append(app)
        return app

    yield make
    for app in opened:
        shut(app)
