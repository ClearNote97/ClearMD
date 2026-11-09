"""Feature 035 on the flet window (spec/features/035_*/spec.md): a row's tone on Results (AC-03),
the presenter's Help (AC-04), Review's full reason under the list (AC-05), where the files are as
text to copy (AC-06), and step 3's two lines (AC-08). The window runs on a page that is not
flet's, on the presenter's fake backend; every text is read from the catalog or the presenter."""

from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest
from support.flet_acceptance import QUIET, Window, click, confirm, converted, pump, windows
from support.gui_fakes import FakeBackend, planned

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.models import BatchPlan, OutcomeStatus, SkippedItem
from clearmd.frontend.flet import FletApp
from clearmd.frontend.flet.views.dialogs.help import HelpDialog
from clearmd.frontend.flet.visuals.theme import role
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.chrome.secondary import ready_line
from clearmd.frontend.presenter.models import RowKind, Tone
from clearmd.frontend.presenter.screens.help import help_sections
from clearmd.i18n import load_catalog

ASK = replace(QUIET, on_existing_output="ask")


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def to_review(app: FletApp) -> None:
    click(app.home.convert.control)
    app.presenter.add_paths([Path("/docs")])
    click(app.actions.primary)
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION, seconds=30)


def to_results(app: FletApp) -> None:
    to_review(app)
    confirm(app)
    pump(app, until=lambda: converted(app) and app.presenter.page == 4, seconds=30)


def mixed_plan() -> BatchPlan:
    skipped = SkippedItem(Path("/docs/deep/notes.md"), SkipReason.ALREADY_MARKDOWN)
    return BatchPlan((planned("a.pdf"), planned("b.pdf", exists=True)), (skipped,), ())


def test_ac_03_each_results_row_has_its_tone_and_word(flet_window: Window) -> None:
    statuses = {"a.pdf": OutcomeStatus.FAILED}
    app = flet_window(FakeBackend(settings=QUIET, statuses=statuses))
    to_results(app)
    result = app.shown.last_result
    assert result is not None and result.rows
    row = result.rows[0]
    assert row.tone is Tone.DANGER
    line = app.results.problems.lines[0]
    assert line.texts[1].value == row.detail  # it opens with its word ("Failed:")
    app.results.problems.clear_selection()  # nothing selected: the row's own colour
    assert all(text.color == role("danger") for text in line.texts)
    app.results.problems.select(0)  # selected: the page's text colour on the selection
    assert all(text.color == role("text") for text in line.texts)


@pytest.mark.parametrize("language", ["en", "es"])
def test_ac_04_help_shows_the_presenters_sections(flet_window: Window, language: str) -> None:
    app = flet_window(FakeBackend(settings=replace(QUIET, language=language)))
    click(app.rail.help)
    dialog = app.dialogs.current
    assert isinstance(dialog, HelpDialog)
    catalog = load_catalog(language)
    shown = dialog.texts()
    sections = help_sections(catalog, drops=False)  # flet takes no dropped files
    assert dialog.sections == sections
    for title, text in sections:
        assert title in shown and text in shown
    assert not any(catalog.text("gui.help.how_drop") in text for text in shown)


def test_ac_05_review_shows_the_full_reason_of_the_first_problem(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=ASK, plan=mixed_plan()))
    to_review(app)
    plan = app.shown.last_plan
    assert plan is not None
    skipped = next(row for row in plan.rows if row.kind is RowKind.SKIPPED)
    current = app.review.files.current()
    assert current is not None and current.payload == skipped  # the first problem, selected
    assert app.review.detail.value == f"{skipped.name}: {skipped.detail}\n{skipped.location}"
    assert current.values[0] == "deep"  # the list's column: the last folder's name only
    exists = next(index for index, line in enumerate(app.review.files.rows())
                  if line.payload.kind is RowKind.EXISTS)  # fmt: skip
    click(app.review.files.lines[exists].frame)  # another row: its own reason in full
    row = app.review.files.rows()[exists].payload
    assert app.review.detail.value == f"{row.name}: {row.detail}\n{row.location}"


def test_ac_06_results_say_where_the_files_are_as_text_to_copy(flet_window: Window) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    to_results(app)
    result = app.shown.last_result
    assert result is not None and result.where
    where = app.results.where
    assert where.visible and where.selectable and where.value == result.where
    assert "OutputMD" in result.where


@pytest.mark.parametrize(("answer", "sent"), [("keep", False), ("overwrite", True)])
def test_ac_08_step_3_says_both_lines(flet_window: Window, answer: str, sent: bool) -> None:
    app = flet_window(FakeBackend(settings=ASK, plan=mixed_plan()))
    to_review(app)
    app.review.answer.choose(answer)
    app.presenter.go_to(3)
    expected = ready_line(app.shown.catalog, app.shown.last_plan, "ask", sent)
    assert expected is not None and "\n" in expected
    first, second = expected.split("\n")
    converting = app.converting
    assert converting.ready_count.value == first
    assert converting.ready_existing.visible and converting.ready_existing.value == second
