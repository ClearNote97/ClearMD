"""Feature 036 in the PySide6 window (spec/features/036_*/spec.md, AC-04): after an unexpected
error the window says only a calm message; "Copy Details" puts the technical lines, without the
user's paths, on the clipboard, then says so and goes away. Strings come from the catalog."""

from collections.abc import Callable
from dataclasses import replace

import pytest
from PySide6.QtGui import QGuiApplication
from support.gui_fakes import FakeBackend
from support.pyside_acceptance import QUIET, pump

from clearmd.frontend.presenter.intents.reset import unexpected
from clearmd.frontend.presenter.state import Tool
from clearmd.frontend.pyside import PySideApp
from clearmd.i18n import load_catalog

Window = Callable[..., PySideApp]
BOOM = RuntimeError("boom at C:\\Users\\Ana\\x.pdf")


def fail(app: PySideApp) -> None:
    unexpected(app.presenter._session, app.presenter._display, BOOM)  # noqa: SLF001 -- the path
    pump(app, seconds=0.05)


@pytest.mark.parametrize(("language", "placeholder"), [("en", "<file>"), ("es", "<archivo>")])
def test_ac_04_copy_details_puts_the_lines_without_paths_on_the_clipboard(
    qt_window: Window, language: str, placeholder: str
) -> None:
    app = qt_window(FakeBackend(settings=replace(QUIET, language=language)))
    app.presenter.choose_tool(Tool.CONVERT)
    catalog = load_catalog(language)
    clipboard = QGuiApplication.clipboard()
    clipboard.setText("")
    fail(app)
    details = app.details
    assert "RuntimeError" not in app.message.text() and app.message.text()
    assert details.isVisible() and details.text() == catalog.text("gui.app.copy_details")
    details.click()
    copied = clipboard.text()
    assert f"{placeholder}.pdf" in copied and "Ana" not in copied
    assert app.message.text() == catalog.text("gui.app.details_copied")
    assert not details.isVisible()


def test_ac_04_a_step_change_hides_the_button(qt_window: Window) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    app.presenter.choose_tool(Tool.CONVERT)
    fail(app)
    assert app.details.isVisible()
    app.presenter.go_to(2)
    assert not app.details.isVisible() and app.message.text() == ""
    fail(app)
    app.view.forget_work()
    assert not app.details.isVisible()
