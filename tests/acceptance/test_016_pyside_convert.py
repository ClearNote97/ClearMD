"""Feature 016 — Review, Convert, Results (AC-03) and closing (AC-07); spec/features/016_*/spec.md.

The PySide6 window runs offscreen, on the presenter's fake backend.
"""

import time
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from support.gui_fakes import FakeBackend, MemoryBackend, planned
from support.pyside_acceptance import (
    QUIET,
    Held,
    confirm,
    converted,
    copy_documents,
    pump,
    to_review,
)

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.models import BatchPlan, OutcomeStatus, SkippedItem
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.models import ProgressView
from clearmd.frontend.pyside import PySideApp
from clearmd.frontend.pyside.views.dialogs.confirm_close import ConfirmCloseDialog

Window = Callable[..., PySideApp]


def test_ac_03_review_shows_the_figures_and_the_skipped_first_with_what_to_do(
    qt_window: Window, tmp_path: Path
) -> None:
    folder = copy_documents(tmp_path / "docs", "sample.docx", "sample.csv")
    (folder / "notes.md").write_text("# notes\n", encoding="utf-8")
    app = qt_window(MemoryBackend(QUIET))
    to_review(app, folder)
    assert app.review.stats.figures() == [
        ("To Convert", "2"),
        ("Skipped", "1"),
        ("Already Exist", "0"),
    ]
    first = app.review.files.rows()[0]
    assert first.name == "notes.md" and first.warning and first.values[1]  # what to do about it
    assert not (tmp_path / "ClearMD_Output").exists()  # nothing is written yet
    assert app.review.files.tree.topLevelItemCount() == 3


def test_ac_03_every_list_row_has_its_icon(qt_window: Window, tmp_path: Path) -> None:
    plan = BatchPlan(
        (planned("a.pdf"), planned("b.docx")),
        (SkippedItem(Path("/docs/n.md"), SkipReason.ALREADY_MARKDOWN),),
        (),
    )
    fake = FakeBackend(plan=plan, statuses={"a.pdf": OutcomeStatus.FAILED}, settings=QUIET)
    app = qt_window(fake)
    to_review(app, tmp_path)
    assert [row.icon for row in app.shown.last_plan.rows] == ["pdf", "docx", "markdown"]  # type: ignore[union-attr]
    confirm(app)
    pump(app, until=lambda: converted(app))
    for tree in (app.review.files.tree, app.results.problems.tree):
        assert tree.topLevelItemCount() and not tree.topLevelItem(0).icon(1).isNull()  # type: ignore[union-attr]


@pytest.mark.parametrize(
    ("setting", "asked"), [("ask", True), ("overwrite", False), ("skip", False)]
)
def test_ac_03_existing_results_are_asked_about_only_with_ask(
    qt_window: Window, tmp_path: Path, setting: str, asked: bool
) -> None:
    plan = BatchPlan((planned("a.pdf", exists=True),), (), ())
    fake = FakeBackend(plan=plan, settings=replace(QUIET, on_existing_output=setting))
    app = qt_window(fake)
    to_review(app, tmp_path)
    assert app.review.existing.isVisible() is asked
    if asked:
        assert app.review.keep.isChecked()  # the safe answer by default
        app.review.overwrite.click()
    confirm(app)
    pump(app, until=lambda: converted(app))
    assert fake.run_calls[-1]["overwrite"](plan.conversions[0]) is (setting != "skip")


def test_ac_03_the_progress_says_where_it_is_and_reassures_on_a_long_file(
    qt_window: Window, tmp_path: Path
) -> None:
    held = Held()
    plan = BatchPlan((planned("Informe.pdf"), planned("b.pdf")), (), ())
    app = qt_window(FakeBackend(plan=plan, settings=QUIET, before_finish=held))
    try:
        to_review(app, tmp_path)
        confirm(app)
        pump(app, until=lambda: app.converting.counter.text() == "1 of 2")
        assert app.converting.file.text().strip() == "Informe.pdf"
        assert app.converting.time_left.text() == "about 2 min left"
        assert app.converting.bar.value() == 0 and app.converting.progress_card.isVisible()
        long_file = ProgressView(
            "1 of 2", "Informe.pdf", 0.5, None, "0:25", "Large files can take a few minutes.", "pdf"
        )
        app.show_progress(long_file)  # what the presenter sends after 15 s on one file
        assert app.converting.long_file.text() == (
            "This file: 0:25 · Large files can take a few minutes."
        )
        assert app.converting.bar.value() == 500
    finally:
        held.gate.set()
    pump(app, until=lambda: converted(app))


def test_ac_03_the_result_tells_the_counts_the_problems_and_the_selected_ones_detail(
    qt_window: Window, tmp_path: Path
) -> None:
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf"), planned("c.pdf")), (), ())
    statuses = {"a.pdf": OutcomeStatus.FAILED, "c.pdf": OutcomeStatus.FAILED}
    settings = replace(QUIET, open_output_when_done=True)
    fake = FakeBackend(plan=plan, statuses=statuses, settings=settings)
    app = qt_window(fake)
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=lambda: converted(app), seconds=30)
    assert app.presenter.state is AppState.FINISHED_WITH_PROBLEMS
    assert app.results.stats.figures()[:3] == [
        ("Converted", "1"),
        ("Skipped", "0"),
        ("Failed", "2"),
    ]
    assert app.results.problems.tree.topLevelItemCount() == 2
    assert "password" in app.results.detail.text() and "a.pdf" in app.results.detail.text()
    app.results.problems.select(1)  # the detail follows the selected problem
    assert "c.pdf" in app.results.detail.text()
    assert fake.opened == [Path("/docs/ClearMD_Output")]  # opened by itself
    app.actions.primary.click()
    assert len(fake.opened) == 2


def test_ac_03_when_every_file_converts_the_result_says_so(
    qt_window: Window, tmp_path: Path
) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=lambda: converted(app))
    assert app.results.all_good.isVisible() and not app.results.problems.isVisible()


def test_ac_07_closing_while_converting_cancels_and_waits_for_the_summary(
    qt_window: Window, tmp_path: Path
) -> None:
    marker = tmp_path / "Resumen_ClearMD.md"
    cancelled: list[bool] = []

    class Slow(FakeBackend):
        def run_batch(self, plan: BatchPlan, **kwargs: Any) -> Any:
            kwargs["cancel"]._event.wait(5)  # converting until cancelled  # noqa: SLF001
            time.sleep(0.3)  # the current file stops, then the summary is written
            marker.write_text("summary", encoding="utf-8")
            cancelled.append(kwargs["cancel"].is_set())
            return super().run_batch(plan, **kwargs)

    app = qt_window(Slow(settings=QUIET))
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=lambda: app.presenter.state is AppState.CONVERTING)
    app.window.close()  # the window's own close button: asked first (feature 038)
    dialog = app.dialogs.current
    assert isinstance(dialog, ConfirmCloseDialog)
    dialog.close_window.click()  # Close
    assert not app.window.isVisible() and not app.closing.closed  # hidden, waiting for the batch
    pump(app, until=lambda: app.closing.closed, seconds=15)
    assert app.closing.closed and marker.is_file() and cancelled == [True]
