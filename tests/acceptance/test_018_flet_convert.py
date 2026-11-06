"""Feature 018 — Review, Convert and Results (AC-03); spec/features/018_*/spec.md.

The flet window is built on a page that is not flet's (no screen), on the presenter's fake backend.
"""

from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest
from support.flet_acceptance import (
    QUIET,
    Held,
    Window,
    click,
    confirm,
    converted,
    copy_documents,
    pump,
    to_review,
    windows,
)
from support.gui_fakes import FakeBackend, MemoryBackend, planned

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.models import BatchPlan, OutcomeStatus, SkippedItem
from clearmd.frontend.flet.visuals.theme import role
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.models import ProgressView


@pytest.fixture
def flet_window() -> Iterator[Window]:
    yield from windows()


def test_ac_03_review_shows_the_figures_and_the_skipped_first_with_what_to_do(
    flet_window: Window, tmp_path: Path
) -> None:
    folder = copy_documents(tmp_path / "docs", "sample.docx", "sample.csv")
    (folder / "notes.md").write_text("# notes\n", encoding="utf-8")
    app = flet_window(MemoryBackend(QUIET))
    to_review(app, folder)
    assert app.review.stats.figures() == [
        ("To convert", "2"),
        ("Skipped", "1"),
        ("Already exist", "0"),
    ]
    first = app.review.files.rows()[0]
    assert first.name == "notes.md" and first.warning and first.values[1]  # what to do about it
    assert app.review.files.lines[0].texts[0].color == role("warning")
    assert not (tmp_path / "ClearMD_Output").exists()  # nothing is written yet
    assert len(app.review.files.lines) == 3


def test_ac_03_every_list_row_has_its_icon(flet_window: Window, tmp_path: Path) -> None:
    plan = BatchPlan(
        (planned("a.pdf"), planned("b.docx")),
        (SkippedItem(Path("/docs/n.md"), SkipReason.ALREADY_MARKDOWN),),
        (),
    )
    fake = FakeBackend(plan=plan, statuses={"a.pdf": OutcomeStatus.FAILED}, settings=QUIET)
    app = flet_window(fake)
    to_review(app, tmp_path)
    assert [str(line.picture.src) for line in app.review.files.lines] == [
        "icons/markdown@2x.png",  # the skipped one first
        "icons/pdf@2x.png",
        "icons/docx@2x.png",
    ]
    confirm(app)
    pump(app, until=lambda: converted(app))
    assert str(app.results.problems.lines[0].picture.src) == "icons/pdf@2x.png"


@pytest.mark.parametrize(
    ("setting", "asked"), [("ask", True), ("overwrite", False), ("skip", False)]
)
def test_ac_03_existing_results_are_asked_about_only_with_ask(
    flet_window: Window, tmp_path: Path, setting: str, asked: bool
) -> None:
    plan = BatchPlan((planned("a.pdf", exists=True),), (), ())
    fake = FakeBackend(plan=plan, settings=replace(QUIET, on_existing_output=setting))
    app = flet_window(fake)
    to_review(app, tmp_path)
    assert app.review.existing.visible is asked
    if asked:
        assert app.review.answer.value == "keep"  # the safe answer by default
        app.review.answer.choose("overwrite")
    confirm(app)
    pump(app, until=lambda: converted(app))
    assert fake.run_calls[-1]["overwrite"](plan.conversions[0]) is (setting != "skip")


def test_ac_03_the_progress_says_where_it_is_and_reassures_on_a_long_file(
    flet_window: Window, tmp_path: Path
) -> None:
    held = Held()
    plan = BatchPlan((planned("Informe.pdf"), planned("b.pdf")), (), ())
    app = flet_window(FakeBackend(plan=plan, settings=QUIET, before_finish=held))
    try:
        to_review(app, tmp_path)
        assert app.converting.ready_count.value == "Ready to convert: 2"  # before it starts
        confirm(app)
        pump(app, until=lambda: app.converting.counter.value == "1 of 2")
        assert app.converting.file.value == "Informe.pdf"
        assert str(app.converting.file_icon.src) == "icons/pdf@2x.png"
        assert app.converting.time_left.value == "about 2 min left"
        assert app.converting.bar.value == 0 and app.converting.progress_card.visible
        assert not app.converting.ready.visible
        long_file = ProgressView(
            "1 of 2", "Informe.pdf", 0.5, None, "0:25", "Large files can take a few minutes.", "pdf"
        )
        app.show_progress(long_file)  # what the presenter sends after 15 s on one file
        assert app.converting.long_file.value == (
            "This file: 0:25 · Large files can take a few minutes."
        )
        assert app.converting.bar.value == 0.5
    finally:
        held.gate.set()
    pump(app, until=lambda: converted(app))


def test_ac_03_the_result_tells_the_counts_the_problems_and_the_selected_ones_detail(
    flet_window: Window, tmp_path: Path
) -> None:
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf"), planned("c.pdf")), (), ())
    statuses = {"a.pdf": OutcomeStatus.FAILED, "c.pdf": OutcomeStatus.FAILED}
    settings = replace(QUIET, open_output_when_done=True)
    fake = FakeBackend(plan=plan, statuses=statuses, settings=settings)
    app = flet_window(fake)
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=lambda: converted(app), seconds=30)
    assert app.presenter.state is AppState.FINISHED_WITH_PROBLEMS
    assert app.results.stats.figures()[:3] == [
        ("Converted", "1"),
        ("Skipped", "0"),
        ("Failed", "2"),
    ]
    assert len(app.results.problems.lines) == 2 and app.results.problems.lines[0].box is None
    assert "password" in str(app.results.detail.value) and "a.pdf" in str(app.results.detail.value)
    click(app.results.problems.lines[1].frame)  # the detail follows the selected problem
    assert "c.pdf" in str(app.results.detail.value)
    assert fake.opened == [Path("/docs/ClearMD_Output")]  # opened by itself
    click(app.actions.primary)
    assert len(fake.opened) == 2


def test_ac_03_when_every_file_converts_the_result_says_so(
    flet_window: Window, tmp_path: Path
) -> None:
    app = flet_window(FakeBackend(settings=QUIET))
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=lambda: converted(app))
    assert app.results.all_good.visible and not app.results.problems.control.visible
