"""Feature 036 on the ttk window (AC-04, D3): after an unexpected error only a calm message shows;
"Copy Details" copies the technical line, without the user's names, then says so and hides."""

from collections.abc import Callable
from dataclasses import replace

import pytest
from support.flet_acceptance import QUIET
from support.gui_fakes import FakeBackend
from support.ttk_unit import pump

from clearmd.frontend.presenter.intents.reset import unexpected
from clearmd.frontend.ttk import TtkApp
from clearmd.i18n import load_catalog


@pytest.mark.parametrize(("language", "file"), [("en", "<file>.pdf"), ("es", "<archivo>.pdf")])
def test_ac_04_copy_details_after_an_unexpected_error(
    window: Callable[..., TtkApp], language: str, file: str
) -> None:
    app = window(FakeBackend(settings=replace(QUIET, language=language)))
    catalog = load_catalog(language)
    app.presenter.go_to(1)
    error = RuntimeError("boom at C:\\Users\\Ana\\x.pdf")
    unexpected(app.presenter._session, app.presenter._display, error)
    pump(app, seconds=0.1)
    assert "RuntimeError" not in app.message.cget("text")  # a calm message only
    button = app.actions.details
    assert button.winfo_ismapped() and button.cget("text") == catalog.text("gui.app.copy_details")
    assert button.cget("takefocus") != 0  # reachable with Tab
    button.invoke()
    pump(app, seconds=0.1)
    copied = app.root.clipboard_get()
    assert file in copied and "Ana" not in copied and "RuntimeError" in copied
    assert app.message.cget("text") == catalog.text("gui.app.details_copied")
    assert not button.winfo_manager()
    unexpected(app.presenter._session, app.presenter._display, error)  # once more, then a step
    pump(app, seconds=0.05)
    assert button.winfo_manager()
    app.presenter.go_to(2)
    pump(app, seconds=0.05)
    assert not button.winfo_manager()  # a step change clears the message and its button
