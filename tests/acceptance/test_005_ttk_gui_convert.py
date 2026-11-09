"""Feature 005 — Converting and the result (AC-09 to AC-12); spec/features/005_*/spec.md.

The window runs under a display (a virtual one when there is none), mostly on a fake backend.
"""

from collections.abc import Callable
from pathlib import Path

from support.gui_fakes import FakeBackend, planned
from support.ttk_acceptance import (
    QUIET,
    Held,
    confirm,
    converted,
    pump,
    replace_settings,
    to_review,
)

from clearmd.backend.schemas.models import BatchPlan, OutcomeStatus
from clearmd.frontend.presenter import AppState
from clearmd.frontend.presenter.models import ProgressView
from clearmd.frontend.ttk import TtkApp


def test_ac_09_the_progress_says_where_it_is_and_reassures_on_a_long_file(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    held = Held()
    plan = BatchPlan((planned("Informe.pdf"), planned("b.pdf")), (), ())
    app = window(FakeBackend(plan=plan, settings=QUIET, before_finish=held))
    try:
        to_review(app, tmp_path)
        confirm(app)
        pump(app, until=lambda: app.converting.counter.cget("text") == "1 of 2")
        assert app.converting.file.cget("text").strip() == "Informe.pdf"
        assert app.converting.time_left.cget("text") == "about 2 min left"
        long_file = ProgressView(
            "1 of 2", "Informe.pdf", 0.0, None, "0:25", "Large files can take a few minutes.", "pdf"
        )
        app.show_progress(long_file)  # what the presenter sends after 15 s on one file
        assert app.converting.long_file.cget("text") == (
            "This file: 0:25 · Large files can take a few minutes."
        )
    finally:
        held.gate.set()
    pump(app, until=lambda: converted(app))


def test_ac_10_cancel_is_always_there_and_stops_at_once(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    held = Held()
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf")), (), ())
    fake = FakeBackend(plan=plan, settings=QUIET, before_finish=held)
    app = window(fake)
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=held.started.is_set)
    pump(app, seconds=0.1)
    assert app.actions.secondary.instate(["!disabled"])
    app.actions.secondary.invoke()
    held.gate.set()
    pump(app, until=lambda: converted(app))
    assert app.presenter.state is AppState.CANCELLED
    assert fake.run_calls[-1]["cancel"].is_set()


# --- After converting ------------------------------------------------------------------------


def test_ac_11_the_result_tells_counts_problems_and_opens_the_folder(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf")), (), ())
    fake = FakeBackend(
        plan=plan,
        statuses={"a.pdf": OutcomeStatus.FAILED},
        settings=replace_settings(QUIET, open_output_when_done=True),
    )
    app = window(fake)
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=lambda: converted(app), seconds=30)
    assert converted(app), (app.presenter.state, app.presenter.page)
    assert app.results.stats.figures()[:3] == [
        ("Converted", "1"),
        ("Skipped", "0"),
        ("Failed", "1"),
    ]
    assert "password" in app.results.detail.cget("text")
    assert fake.opened == []  # with a problem it does not open by itself (039, F1-06)
    app.actions.primary.invoke()
    assert fake.opened == [Path("/docs/ClearMD_Output")]


def test_ac_12_one_failed_file_never_stops_the_batch(
    window: Callable[..., TtkApp], tmp_path: Path
) -> None:
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf"), planned("c.pdf")), (), ())
    app = window(FakeBackend(plan=plan, statuses={"a.pdf": OutcomeStatus.FAILED}, settings=QUIET))
    to_review(app, tmp_path)
    confirm(app)
    pump(app, until=lambda: converted(app))
    assert app.presenter.state is AppState.FINISHED_WITH_PROBLEMS
    assert ("Converted", "2") in app.results.stats.figures()
