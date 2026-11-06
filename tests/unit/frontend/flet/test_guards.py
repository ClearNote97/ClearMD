"""The flet window's guards (feature 018): what is asked at the wrong moment does nothing — before
the presenter starts, with a dialog open, while converting, closing twice."""

from pathlib import Path

import pytest
from support.flet_acceptance import QUIET, Held, confirm, page_of, pump, shut, to_review
from support.flet_fake_page import FakePage
from support.gui_fakes import FakeBackend

from clearmd.frontend.flet import FletApp


def test_before_the_presenter_starts_nothing_opens() -> None:
    app = FletApp(FakePage(), FakeBackend(settings=QUIET))
    with pytest.raises(RuntimeError):
        app.shown.need_catalog()
    app.dialogs.show_settings()
    assert app.dialogs.current is None


def test_with_a_dialog_open_no_other_opens_and_the_primary_waits(tmp_path: Path) -> None:
    app = FletApp(FakePage(), FakeBackend(settings=QUIET))
    app.start()
    app.presenter.add_paths([tmp_path])
    app.dialogs.show_help()
    help_dialog = app.dialogs.current
    app.dialogs.welcome(("1. a",))
    app.primary_button.press()
    assert app.dialogs.current is help_dialog and app.presenter.page == 1
    shut(app)


def test_while_converting_the_pickers_stay_shut(tmp_path: Path) -> None:
    held = Held()
    app = FletApp(FakePage(), FakeBackend(settings=QUIET, before_finish=held))
    app.start()
    try:
        to_review(app, tmp_path)
        confirm(app)
        pump(app, until=held.started.is_set)
        pump(app, seconds=0.05)
        app.pickers.add_files()
        app.pickers.add_folder()
        app.pickers.pick_output_folder()
        assert page_of(app).asked == []
    finally:
        held.gate.set()
    shut(app)


def test_closing_twice_closes_once() -> None:
    app = FletApp(FakePage(), FakeBackend(settings=QUIET))
    app.start()
    app.close()
    app.closing.destroy()
    app.close()
    assert app.closing.closed and page_of(app).destroyed
