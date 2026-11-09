"""Feature 035 in the PySide6 window (spec/features/035_*/spec.md): Help from the presenter's
sections (AC-04), Review's detail line (AC-05), where the results are as text (AC-06), Results'
rows in their own tone (AC-03), and step 3's two lines (AC-08). Strings come from the catalog."""

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt
from support.gui_fakes import FakeBackend, planned
from support.pyside_acceptance import QUIET, confirm, converted, pump, to_review

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.models import BatchPlan, OutcomeStatus, SkippedItem
from clearmd.frontend.presenter.chrome.secondary import ready_line
from clearmd.frontend.presenter.screens.help import help_sections
from clearmd.frontend.pyside import PySideApp
from clearmd.frontend.pyside.views.dialogs.help import HelpDialog
from clearmd.i18n import load_catalog

Window = Callable[..., PySideApp]
DOCS = Path("/docs")
SELECTABLE = Qt.TextInteractionFlag.TextSelectableByMouse


def plan_with_problems() -> BatchPlan:
    skipped = SkippedItem(DOCS / "deep" / "figures.zip", SkipReason.ZIP_ARCHIVE)
    return BatchPlan((planned("a.pdf"), planned("b.pdf", exists=True)), (skipped,), ())


def to_results(app: PySideApp, folder: Path) -> None:
    app.home.convert.button.click()
    to_review(app, folder)
    confirm(app)
    pump(app, until=lambda: converted(app) and app.presenter.page == 4, seconds=10)


def test_ac_04_help_shows_the_presenters_sections_and_the_drop_sentence(
    qt_window: Window,
) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    app.rail.help.click()
    dialog = app.dialogs.current
    assert isinstance(dialog, HelpDialog)
    catalog = load_catalog("en")
    sections = help_sections(catalog, drops=True)  # this window takes dropped files
    assert dialog.titles == [title for title, _ in sections]
    assert dialog.texts == [text for _, text in sections]
    drop = catalog.text("gui.help.how_drop")
    assert drop and any(drop in text for text in dialog.texts)
    dialog.close_dialog()


def test_ac_05_review_shows_the_selected_rows_reason_and_folder_in_full(
    qt_window: Window, tmp_path: Path
) -> None:
    app = qt_window(FakeBackend(settings=QUIET, plan=plan_with_problems()))
    app.home.convert.button.click()
    to_review(app, tmp_path)
    review = app.review
    plan = app.shown.last_plan
    assert plan is not None
    first = review.files.current()  # the first row with a problem is selected at first
    assert first is not None and first.name == "figures.zip" and first.warning
    skipped = next(row for row in plan.rows if row.name == "figures.zip")
    assert first.values[0] == Path(skipped.location).name  # the folder's last name in the list
    assert skipped.detail in review.detail.text() and skipped.location in review.detail.text()
    assert review.detail.textInteractionFlags() & SELECTABLE
    names = [row.name for row in review.files.rows()]
    review.files.select(names.index("b.pdf"))
    existing = next(row for row in plan.rows if row.name == "b.pdf")
    assert existing.detail in review.detail.text()


def test_ac_06_results_say_where_the_files_are_as_text_to_copy(
    qt_window: Window, tmp_path: Path
) -> None:
    app = qt_window(FakeBackend(settings=QUIET))
    to_results(app, tmp_path)
    result = app.shown.last_result
    assert result is not None and result.where
    where = app.results.where
    assert where.isVisible() and where.text() == result.where and "OutputMD" in where.text()
    assert where.textInteractionFlags() & SELECTABLE


def test_ac_03_each_result_row_has_its_tone(qt_window: Window, tmp_path: Path) -> None:
    plan = BatchPlan(
        (planned("a.pdf"), planned("bad.pdf")),
        (SkippedItem(DOCS / "x.zip", SkipReason.ZIP_ARCHIVE),),
        (),
    )
    backend = FakeBackend(settings=QUIET, plan=plan, statuses={"bad.pdf": OutcomeStatus.FAILED})
    app = qt_window(backend)
    to_results(app, tmp_path)
    palette = app.shown.palette
    tree = app.results.problems.tree
    catalog = load_catalog("en")
    for index, row in enumerate(app.results.problems.rows()):
        item = tree.topLevelItem(index)
        assert item is not None
        colour = item.foreground(1).color().name().upper()
        if row.danger:
            assert colour == palette.danger.upper() and row.name == "bad.pdf"
        else:
            assert colour == palette.warning.upper() and row.name == "x.zip"
    words = {row.name: row.values[0] for row in app.results.problems.rows()}
    assert words["bad.pdf"].startswith(catalog.text("gui.result.word_failed"))
    assert words["x.zip"].startswith(catalog.text("gui.result.word_skipped"))


def test_ac_08_step_3_says_how_many_are_written_and_the_existing_results_fate(
    qt_window: Window, tmp_path: Path
) -> None:
    app = qt_window(FakeBackend(settings=QUIET, plan=plan_with_problems()))
    app.home.convert.button.click()
    to_review(app, tmp_path)
    catalog = load_catalog("en")
    plan = app.shown.last_plan
    for answer, radio in (("changed", app.review.changed), (True, app.review.overwrite)):
        app.presenter.go_to(2)
        radio.click()
        app.presenter.go_to(3)
        expected = ready_line(catalog, plan, "ask", answer)
        assert expected is not None and "\n" in expected
        first, second = expected.split("\n", 1)
        converting = app.converting
        assert converting.ready_count.text() == first
        assert converting.ready_existing.isVisible() and converting.ready_existing.text() == second
