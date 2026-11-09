"""Feature 035 on the ttk window (spec/features/035_*): honest signals and help — each Results row
with its word and tone (AC-03), Help as the presenter gives it (AC-04), Review's full detail
(AC-05), where the files are as text (AC-06), the list's scroll bar and a thousand rows (AC-07),
step 3's two lines (AC-08). Strings come from the catalog or the presenter, never copies."""

import time
from collections.abc import Callable
from pathlib import Path

from support.flet_acceptance import QUIET
from support.gui_fakes import FakeBackend, planned
from support.ttk_unit import confirm, pump

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.models import BatchPlan, OutcomeStatus, SkippedItem
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.chrome.secondary import ready_line
from clearmd.frontend.presenter.screens.help import help_sections
from clearmd.frontend.ttk import TtkApp
from clearmd.frontend.ttk.components.file_list import ListRow
from clearmd.frontend.ttk.views.dialogs.help import help_dialog
from clearmd.i18n import load_catalog

DOCS = Path("/docs/Informes/2026")
PLAN = BatchPlan(
    (planned("a.pdf", folder=DOCS), planned("b.docx", folder=DOCS, exists=True)),
    (SkippedItem(DOCS / "notas.zip", SkipReason.ZIP_ARCHIVE),),
    (),
)


def reviewed(app: TtkApp) -> None:
    app.presenter.add_paths([DOCS])
    app.presenter.analyze()
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)


def to_results(app: TtkApp) -> None:
    reviewed(app)
    confirm(app)
    pump(app, until=lambda: app.presenter.page == 4)
    pump(app, seconds=0.1)


def test_ac_03_each_results_row_has_its_word_and_its_tone(window: Callable[..., TtkApp]) -> None:
    app = window(FakeBackend(plan=PLAN, settings=QUIET, statuses={"a.pdf": OutcomeStatus.FAILED}))
    to_results(app)
    assert app.last_result is not None
    tree = app.results.problems.tree
    for item, row in zip(tree.get_children(), app.last_result.rows, strict=True):
        assert tree.item(item, "tags") == (row.tone.value,)  # "danger" or "warning"
        assert row.detail.split(":")[0] in {"Failed", "Stopped", "Left out"}  # a word first
    tones = {row.tone.value for row in app.last_result.rows}
    assert tones == {"danger", "warning"}
    assert str(tree.tag_configure("danger", "foreground")) == app.palette.danger
    assert str(tree.tag_configure("warning", "foreground")) == app.palette.warning


def test_ac_04_help_shows_the_presenter_s_sections_and_drop_only_when_it_drops(
    window: Callable[..., TtkApp],
) -> None:
    app = window(FakeBackend(settings=QUIET))
    catalog = load_catalog("en")
    drop = catalog.text("gui.help.how_drop")
    for drops in (True, False):
        dialog = help_dialog(app.root, catalog, app.palette, app.fonts, lambda: None, drops=drops)
        shown = [(title.cget("text"), text.cget("text")) for title, text in dialog.sections]
        assert shown == list(help_sections(catalog, drops=drops))
        assert any(drop in text for _, text in shown) is drops
        dialog.destroy()
    app.rail.help.invoke()  # the window's own: dropping told only if tkdnd is loaded
    pump(app, seconds=0.2)
    sections = [text.cget("text") for _, text in app.dialog.sections]  # type: ignore[union-attr]
    assert any(drop in text for text in sections) is app.drops


def test_ac_05_review_shows_the_selected_row_in_full(window: Callable[..., TtkApp]) -> None:
    app = window(FakeBackend(plan=PLAN, settings=QUIET))
    reviewed(app)
    pump(app, seconds=0.1)
    current = app.review.files.current()
    assert current is not None and current.name == "notas.zip"  # the first row with a problem
    row = current.payload
    detail = app.review.detail.cget("text")
    assert row.detail in detail and row.location in detail  # the reason, what to do, the folder
    assert app.review.detail.winfo_ismapped()
    tree = app.review.files.tree
    assert all(tree.item(item, "values")[0] == "2026" for item in tree.get_children())


def test_ac_06_results_say_where_the_files_are_as_text(window: Callable[..., TtkApp]) -> None:
    app = window(FakeBackend(plan=PLAN, settings=QUIET))
    to_results(app)
    assert app.last_result is not None and app.last_result.where
    where = app.results.where
    assert where.winfo_ismapped() and where.text() == app.last_result.where
    assert "OutputMD" in where.text()
    where.tag_add("sel", "1.0", "end-1c")  # selectable, so it can be copied
    assert where.get("sel.first", "sel.last") == app.last_result.where


def test_ac_07_the_list_shows_its_scroll_bar_and_a_thousand_rows(
    window: Callable[..., TtkApp],
) -> None:
    plan = BatchPlan(tuple(planned(f"{n}.pdf", folder=DOCS) for n in range(9)), (), ())
    app = window(FakeBackend(plan=plan, settings=QUIET))
    app.root.geometry("800x624")
    reviewed(app)
    pump(app, seconds=0.5)
    files = app.review.files
    assert float(files.tree.yview()[1]) < 1.0  # rows are hidden…
    assert files.scroll.winfo_ismapped() and files.scroll.winfo_width() > 1  # …and the bar shows
    rows = [ListRow("pdf", f"file {n}.pdf", (str(DOCS),), payload=n) for n in range(1000)]
    app.presenter.go_to(1)
    start = time.perf_counter()
    app.main.inputs.show(rows)
    app.root.update()
    assert time.perf_counter() - start < 1.5
    assert len(app.main.inputs.names()) == 1000


def test_ac_08_step_3_says_what_will_be_written_on_two_lines(
    window: Callable[..., TtkApp],
) -> None:
    app = window(FakeBackend(plan=PLAN, settings=QUIET))
    reviewed(app)
    app.review.changed.invoke()  # Review's answer: replace those whose original changed
    app.presenter.go_to(3)
    pump(app, seconds=0.1)
    catalog = load_catalog("en")
    expected = ready_line(catalog, app.last_plan, "ask", "changed")
    assert expected is not None and "\n" in expected
    first, existing = expected.split("\n", 1)
    count, more = app.converting.ready_count, app.converting.ready_existing
    assert count.cget("text") == first and count.winfo_ismapped()
    assert more.cget("text") == existing and more.winfo_ismapped()  # the second line too
