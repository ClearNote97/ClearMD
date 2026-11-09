"""Feature 036 in the flet window (spec/features/036_*/spec.md, AC-04): after an unexpected error
the window says only a calm message; "Copy Details" puts the technical lines, without the user's
paths, on the clipboard, then says so and goes away. The window runs on a page that is not
flet's (its clipboard a list); strings come from the catalog."""

from collections.abc import Iterator
from dataclasses import replace

import pytest
from support.flet_acceptance import QUIET, Window, click, page_of, windows
from support.gui_fakes import FakeBackend

from clearmd.frontend.flet import FletApp
from clearmd.frontend.presenter.intents.reset import unexpected
from clearmd.frontend.presenter.state import Tool
from clearmd.i18n import load_catalog

BOOM = RuntimeError("boom at C:\\Users\\Ana\\x.pdf")


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def fail(app: FletApp) -> None:
    unexpected(app.presenter._session, app.presenter._display, BOOM)  # noqa: SLF001 -- the path


@pytest.mark.parametrize(("language", "placeholder"), [("en", "<file>"), ("es", "<archivo>")])
def test_ac_04_copy_details_puts_the_lines_without_paths_on_the_clipboard(
    flet_window: Window, language: str, placeholder: str
) -> None:
    app = flet_window(FakeBackend(settings=replace(QUIET, language=language)))
    app.presenter.choose_tool(Tool.CONVERT)
    catalog = load_catalog(language)
    fail(app)
    line = app.message_line
    message = str(line.text.value)
    assert message == catalog.text("gui.app.unexpected_error") and "RuntimeError" not in message
    assert line.control.visible and line.text.visible
    assert line.details.visible and line.details.content == catalog.text("gui.app.copy_details")
    click(line.details)
    copied = page_of(app).clipboard
    assert len(copied) == 1 and f"{placeholder}.pdf" in copied[0] and "Ana" not in copied[0]
    assert "flet" in copied[0]  # the window it happened in
    assert line.text.value == catalog.text("gui.app.details_copied")
    assert not line.details.visible


def test_ac_04_a_step_change_and_a_dropped_result_hide_the_button(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    app.presenter.choose_tool(Tool.CONVERT)
    fail(app)
    line = app.message_line
    assert line.details.visible
    app.presenter.go_to(2)  # another step: the message and its button go
    assert not line.details.visible and line.text.value == "" and not line.control.visible
    app.presenter.go_to(1)
    fail(app)
    app.view.forget_work()
    app.view.show_message("")
    assert not line.details.visible


def test_ac_04_a_failing_clipboard_leaves_the_message_as_it_was(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    app.presenter.choose_tool(Tool.CONVERT)
    fail(app)
    page_of(app).clipboard_fails = True
    line = app.message_line
    before = line.text.value
    click(line.details)
    assert line.text.value == before and line.details.visible  # the presenter caught it
