"""Review, convert and results through the window (005, T05)."""

import threading
from pathlib import Path

from support.gui_close import shut
from support.gui_fakes import FakeBackend, planned
from support.ttk_unit import confirm, convert_more, press_enter, pump, shown

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.models import BatchPlan, OutcomeStatus, SkippedItem
from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.presenter import AppState
from clearmd.frontend.ttk import TtkApp

# --- Review, convert, results (T05) --------------------------------------------------------------


def test_review_shows_the_figures_and_each_file_then_converting_ends_in_results(
    display: str, tmp_path: Path
) -> None:
    plan = BatchPlan(
        (planned("a.pdf"), planned("b.docx", exists=True)),
        (SkippedItem(Path("/docs/notes.md"), SkipReason.ALREADY_MARKDOWN),),
        (),
    )
    fake = FakeBackend(plan=plan, settings=Settings(show_welcome=False, theme="light"))
    app = TtkApp(fake)
    try:
        app.start()
        app.presenter.add_paths([tmp_path])
        app.actions.primary.invoke()
        pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
        assert shown(app) is app.review
        assert app.review.stats.figures() == [
            ("To convert", "2"),
            ("Skipped", "1"),
            ("Already exist", "1"),
        ]
        assert app.review.files.names() == ["notes.md", "a.pdf", "b.docx"]  # attention first
        assert app.review.existing.winfo_ismapped()  # the setting is "ask"
        app.review.decision.set("overwrite")
        confirm(app)
        pump(app, until=lambda: app.presenter.state is AppState.FINISHED)
        assert fake.run_calls[-1]["overwrite"](plan.conversions[1]) is True
        assert shown(app) is app.results
        assert app.rail.step_texts()[3] == "> Results"
        assert ("Converted", "2") in app.results.stats.figures()
        assert app.results.problems.names() == ["notes.md"]  # skipped: said why, with what to do
        assert fake.opened  # the folder opens by itself (open_output_when_done)
        convert_more(app)
        assert shown(app) is app.main and app.main.inputs.names() == [f"{tmp_path.name}/"]
    finally:
        shut(app)


def test_progress_shows_the_file_and_cancel_stops(display: str, tmp_path: Path) -> None:
    gate = threading.Event()
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf")), (), ())
    fake = FakeBackend(plan=plan, settings=Settings(show_welcome=False))

    def hold() -> None:  # the first file is converting until the test lets it go
        gate.wait(5)

    fake.before_finish = hold
    app = TtkApp(fake)
    try:
        app.start()
        app.presenter.add_paths([tmp_path])
        app.actions.primary.invoke()
        pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
        confirm(app)
        pump(app, until=lambda: app.converting.counter.cget("text") == "1 of 2")
        assert shown(app) is app.converting
        assert app.converting.file.cget("text").strip() == "a.pdf"
        assert app.actions.secondary.instate(["!disabled"])
        app.actions.secondary.invoke()
        gate.set()
        pump(app, until=lambda: app.presenter.state is AppState.CANCELLED)
        assert app.presenter.state is AppState.CANCELLED and shown(app) is app.results
    finally:
        gate.set()
        shut(app)


def test_a_clean_batch_says_every_file_was_converted(display: str, tmp_path: Path) -> None:
    app = TtkApp(FakeBackend(settings=Settings(show_welcome=False)))
    try:
        app.start()
        app.presenter.add_paths([tmp_path])
        app.actions.primary.invoke()
        pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
        press_enter(app)  # Enter on Review: Next
        pump(app, until=lambda: app.presenter.page == 3)
        press_enter(app)  # Enter on Convert: Convert
        pump(app, until=lambda: app.presenter.state is AppState.FINISHED)
        pump(app, seconds=0.1)
        assert app.results.all_good.winfo_ismapped()
        assert not app.results.problems.winfo_ismapped()
    finally:
        shut(app)


def test_problems_are_listed_in_the_results(display: str, tmp_path: Path) -> None:
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf")), (), ())
    fake = FakeBackend(
        plan=plan,
        statuses={"a.pdf": OutcomeStatus.FAILED},
        settings=Settings(show_welcome=False, open_output_when_done=False),
    )
    app = TtkApp(fake)
    try:
        app.start()
        app.presenter.add_paths([tmp_path])
        app.actions.primary.invoke()
        pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
        confirm(app)
        pump(app, until=lambda: app.presenter.state is AppState.FINISHED_WITH_PROBLEMS)
        assert app.results.problems.names() == ["a.pdf"]
        assert app.results.detail.cget("text") == (
            "a.pdf: This file is password-protected. Remove the password and try again."
        )
        assert not app.results.all_good.winfo_ismapped()
        app.actions.primary.invoke()
        assert fake.opened
    finally:
        shut(app)
