"""Regressions found in the code review of 005 (C-*, A3, A4)."""

import time
import tkinter as tk
from pathlib import Path
from typing import Any

import pytest
from support.gui_close import shut
from support.gui_fakes import FakeBackend, planned
from support.ttk_unit import confirm, pump

from clearmd.backend.schemas.models import BatchPlan, OutcomeStatus
from clearmd.backend.schemas.settings import Settings, SettingsProblem, SettingsWarning
from clearmd.frontend.presenter import AppState
from clearmd.frontend.ttk import TtkApp
from clearmd.frontend.ttk.views import dialogs

# --- Review of 005 (code review C-*) -------------------------------------------------------------


def run_until_closed(app: TtkApp, seconds: float = 10.0) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            app.root.update()
            if not app.root.winfo_exists():
                return True
        except tk.TclError:
            return True  # destroyed
        time.sleep(0.01)
    return False


def test_c1_closing_while_converting_waits_for_the_summary(display: str, tmp_path: Path) -> None:
    marker = tmp_path / "Resumen_ClearMD.md"

    class Slow(FakeBackend):
        def run_batch(self, plan: BatchPlan, **kwargs: Any) -> Any:
            kwargs["cancel"]._event.wait(5)  # converting until cancelled
            time.sleep(0.3)  # the current file stops, then the summary is written
            marker.write_text("summary", encoding="utf-8")
            return super().run_batch(plan, **kwargs)

    app = TtkApp(Slow(settings=Settings(show_welcome=False)))
    app.start()
    app.presenter.add_paths([tmp_path])
    app.actions.primary.invoke()
    pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
    confirm(app)
    pump(app, until=lambda: app.presenter.state is AppState.CONVERTING)
    shut(app)
    assert run_until_closed(app)
    assert marker.is_file()


def test_c2_an_unexpected_error_stays_on_screen(display: str, tmp_path: Path) -> None:
    app = TtkApp(FakeBackend(settings=Settings(show_welcome=False), plan_error=RuntimeError("x")))
    try:
        app.start()
        app.presenter.add_paths([tmp_path])
        app.actions.primary.invoke()
        pump(app, until=lambda: app.presenter.state is AppState.READY and app.last_plan is None)
        pump(app, seconds=0.2)
        assert "Something unexpected went wrong" in app.message.cget("text")
    finally:
        shut(app)


def test_c3_settings_warnings_at_start_are_on_screen(display: str) -> None:
    warnings = (SettingsWarning("colour", SettingsProblem.UNKNOWN_KEY),)
    app = TtkApp(FakeBackend(settings=Settings(show_welcome=False), warnings=warnings))
    try:
        app.start()
        pump(app, seconds=0.2)
        assert "colour" in app.message.cget("text")
        assert int(app.message.cget("wraplength")) > 0  # C-12: long messages wrap
    finally:
        shut(app)


def test_c5_a_theme_change_keeps_the_selected_row(app: TtkApp, tmp_path: Path) -> None:
    app.presenter.add_paths([tmp_path / "a.pdf", tmp_path / "b.pdf"])
    tree = app.main.inputs.tree
    tree.selection_set(tree.get_children()[1])
    app.apply_theme("dark")
    assert [tree.index(item) for item in tree.selection()] == [1]


def test_c9_closing_with_the_welcome_open_keeps_its_answer(display: str) -> None:
    fake = FakeBackend(settings=Settings(show_welcome=True))
    app = TtkApp(fake)
    app.start()
    pump(app, until=lambda: app.dialog is not None)
    assert isinstance(app.dialog, dialogs.welcome.WelcomeDialog)
    app.dialog.dont_show.set(True)
    shut(app)
    assert fake.saved[-1].show_welcome is False


def test_a3_a_settings_save_keeps_the_selected_problem(display: str, tmp_path: Path) -> None:
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf")), (), ())
    statuses = {"a.pdf": OutcomeStatus.FAILED, "b.pdf": OutcomeStatus.FAILED}
    app = TtkApp(FakeBackend(plan=plan, statuses=statuses, settings=Settings(show_welcome=False)))
    try:
        app.start()
        app.presenter.add_paths([tmp_path])
        app.actions.primary.invoke()
        pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
        confirm(app)
        pump(app, until=lambda: app.presenter.state is AppState.FINISHED_WITH_PROBLEMS)
        tree = app.results.problems.tree
        tree.selection_set(tree.get_children()[1])
        pump(app, seconds=0.1)
        app.presenter.save_settings(replace_settings(app.presenter.settings, recursive=False))
        pump(app, seconds=0.1)
        assert [tree.index(item) for item in tree.selection()] == [1]
        assert app.results.detail.cget("text").startswith("b.pdf")
    finally:
        shut(app)


def test_a4_a_plan_shown_again_keeps_the_answer_about_existing_results(
    display: str, tmp_path: Path
) -> None:
    plan = BatchPlan((planned("a.pdf", exists=True),), (), ())
    app = TtkApp(FakeBackend(plan=plan, settings=Settings(show_welcome=False)))
    try:
        app.start()
        app.presenter.add_paths([tmp_path])
        app.actions.primary.invoke()
        pump(app, until=lambda: app.presenter.state is AppState.WAITING_DECISION)
        app.review.decision.set("overwrite")
        assert app.last_plan is not None
        app.show_plan(app.last_plan)  # the same plan again (a language change)
        assert app.review.decision.get() == "overwrite"
    finally:
        shut(app)


def replace_settings(settings: Settings, **changes: Any) -> Settings:
    from dataclasses import replace

    return replace(settings, **changes)


def test_without_tkdnd_the_window_still_works_without_dropping(
    display: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from tkinterdnd2 import TkinterDnD

    def unavailable() -> None:
        tk.Tk()  # as in tkinterdnd2: the interpreter exists before loading tkdnd fails
        raise RuntimeError("Unable to load tkdnd library.")  # e.g. a Tk it was not built for

    monkeypatch.setattr(TkinterDnD, "Tk", unavailable)
    app = TtkApp(FakeBackend(settings=Settings(show_welcome=False)))
    try:
        app.start()
        assert app.drops is False
        app.presenter.add_paths([tmp_path])
        assert app.main.inputs.names() == [f"{tmp_path.name}/"]
        assert all(
            app.main.inputs.tree.item(i, "image") for i in app.main.inputs.tree.get_children()
        )
    finally:
        shut(app)
