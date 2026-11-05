"""The ``app`` fixture: a ttk window on a fake backend, light theme, no welcome."""

from collections.abc import Iterator

import pytest
from support.gui_close import shut
from support.gui_fakes import FakeBackend
from support.ttk_unit import pump

from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.ttk import TtkApp


@pytest.fixture
def app(display: str) -> Iterator[TtkApp]:
    window = TtkApp(FakeBackend(settings=Settings(show_welcome=False, theme="light")))
    window.start()
    pump(window, seconds=0.2)
    yield window
    shut(window)
