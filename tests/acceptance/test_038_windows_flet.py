"""Feature 038 on the flet window (audit v2): closing asks only while a task runs (AC-06), and an
unexpected error during a task lands on Results with "Copy Details" (AC-04). The window runs on a
page that is not flet's, on the presenter's fake backend; every text comes from the catalog."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from support.flet_acceptance import (
    QUIET,
    Held,
    Window,
    click,
    confirm,
    page_of,
    pump,
    to_review,
    windows,
)
from support.gui_fakes import FakeBackend, planned

from clearmd.backend.schemas.models import BatchPlan
from clearmd.frontend.flet import FletApp
from clearmd.frontend.flet.views.dialogs.close_question import CloseQuestionDialog
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.intents.reset import unexpected
from clearmd.i18n import load_catalog


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def converting(flet_window: Window, tmp_path: Path, held: Held) -> FletApp:
    plan = BatchPlan((planned("a.pdf", folder=tmp_path),), (), ())  # its folder is tmp_path
    app = flet_window(FakeBackend(settings=QUIET, plan=plan, before_finish=held))
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=held.started.is_set)
    assert app.presenter.state is AppState.CONVERTING
    return app


def test_ac_06_closing_during_a_task_asks_once(flet_window: Window, tmp_path: Path) -> None:
    held = Held()
    app = converting(flet_window, tmp_path, held)
    page = page_of(app)
    catalog = load_catalog("en")
    try:
        page.close_button()
        question = app.dialogs.current
        assert isinstance(question, CloseQuestionDialog)
        assert question.title.value == catalog.text("gui.close.title")
        assert catalog.text("gui.close.body") in question.texts()
        assert question.keep.content == catalog.text("gui.close.keep")
        assert question.close.content == catalog.text("gui.close.close")
        page.close_button()  # asked once: no second question
        assert app.dialogs.current is question and len(page.dialogs) == 1
        page.press("Escape")  # Keep Working (Esc): nothing happens, the task goes on
        assert app.dialogs.current is None and not page.hidden and not app.closing.closed
        assert app.presenter.state is AppState.CONVERTING
        page.close_button()
        question = app.dialogs.current
        assert isinstance(question, CloseQuestionDialog)
        click(question.keep)  # Keep Working, by its button
        assert app.presenter.state is AppState.CONVERTING and not page.hidden
        page.close_button()
        question = app.dialogs.current
        assert isinstance(question, CloseQuestionDialog)
        click(question.close)  # Close: cancel, hide, wait for the batch
        assert page.hidden and app.presenter.state is AppState.CONVERTING
    finally:
        held.gate.set()
    pump(app, until=lambda: app.closing.closed, seconds=15)
    assert app.closing.closed and page.destroyed


def test_ac_06_cancel_and_closing_when_idle_never_ask(flet_window: Window, tmp_path: Path) -> None:
    held = Held()
    app = converting(flet_window, tmp_path, held)
    click(app.actions.secondary)  # Cancel, on the action bar
    held.gate.set()
    assert app.dialogs.current is None
    pump(app, until=lambda: app.presenter.state is not AppState.CONVERTING, seconds=15)
    idle = flet_window(FakeBackend(settings=QUIET))
    page_of(idle).close_button()
    assert idle.dialogs.current is None and idle.closing.closed and page_of(idle).destroyed


def test_ac_04_an_error_during_a_task_shows_results(flet_window: Window, tmp_path: Path) -> None:
    held = Held()
    app = converting(flet_window, tmp_path, held)
    (tmp_path / "ClearMD_Output").mkdir(exist_ok=True)  # what was written so far
    catalog = load_catalog("en")
    try:
        unexpected(app.presenter._session, app.presenter._display, RuntimeError("boom"))  # noqa: SLF001
        assert app.presenter.page == 4 and app.pages[3].visible
        assert app.presenter.state is AppState.FINISHED_WITH_PROBLEMS
        line = app.message_line
        assert line.text.value == catalog.text("gui.app.unexpected_error")
        assert line.details.visible  # not cleared by the page change: shown after it
        assert line.details.content == catalog.text("gui.app.copy_details")
        result = app.shown.last_result
        assert result is not None and not result.rows and result.folders  # the presenter's
        assert app.results.where.value == result.where  # shown as the presenter says it
        assert app.results.where.visible is bool(result.where)
        assert not app.actions.primary.disabled  # Open Results Folder: the folder exists
    finally:
        held.gate.set()
