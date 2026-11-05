"""The PySide6 window starts and draws (feature 016): offscreen, with the presenter's fake backend.
Its full acceptance comes with 016; during refactor R01 this guards that it still builds."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # before Qt is loaded: no display needed

from support.gui_fakes import FakeBackend  # noqa: E402

from clearmd.backend.schemas.settings import Settings  # noqa: E402
from clearmd.frontend.pyside import PySideApp  # noqa: E402
from clearmd.frontend.pyside.app import application  # noqa: E402


def test_the_window_builds_draws_and_closes() -> None:
    app = application()
    window = PySideApp(FakeBackend(settings=Settings(show_welcome=False)))
    window.start()
    app.processEvents()
    assert not window.grab().isNull()
    assert window.rail.step_texts()[0].startswith("> ")
    window.close_window()
    app.processEvents()
    assert window.closed
