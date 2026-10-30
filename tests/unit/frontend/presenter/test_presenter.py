"""The presenter (005, T03): states, intents and texts, with a fake view and a fake backend."""

import os
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import pytest
from support.gui_fakes import FakeBackend, planned

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.formats import Strategy
from clearmd.backend.schemas.models import (
    BatchPlan,
    OutcomeStatus,
    SkippedItem,
)
from clearmd.backend.schemas.settings import Settings, SettingsProblem, SettingsWarning
from clearmd.frontend.presenter import Action, AppState, OutputMode, Presenter
from clearmd.frontend.presenter.models import RowKind, Stat, Tone
from clearmd.i18n import Catalog


def absolute(path: str) -> Path:
    """How the presenter keeps an input: absolute (on Windows, with the current drive)."""
    return Path(os.path.abspath(path))


# --- Fakes ---------------------------------------------------------------------------------------


@dataclass
class FakeView:
    """Records what the presenter shows; callbacks scheduled with ``after`` run when drained."""

    calls: list[tuple[str, Any]] = field(default_factory=list)
    pending: list[tuple[int, Callable[[], None]]] = field(default_factory=list)
    threads: list[int] = field(default_factory=list)

    def after(self, milliseconds: int, callback: Callable[[], None]) -> None:
        self.pending.append((milliseconds, callback))

    def drain(self, *, timers: bool = False) -> None:
        """Run the scheduled callbacks (the UI loop); timers (ms > 0) only when asked."""
        while True:
            ready = [entry for entry in self.pending if timers or entry[0] == 0]
            if not ready:
                return
            for entry in ready:
                self.pending.remove(entry)
                entry[1]()
            if timers:
                return

    def last(self, name: str) -> Any:
        return next(value for call, value in reversed(self.calls) if call == name)

    def _record(self, name: str, value: Any) -> None:
        self.threads.append(threading.get_ident())
        self.calls.append((name, value))

    def show_state(self, state: Any) -> None:
        self._record("state", state)

    def show_inputs(self, rows: Any) -> None:
        self._record("inputs", rows)

    def show_output_choice(self, choice: Any) -> None:
        self._record("output", choice)

    def show_scan(self, text: str) -> None:
        self._record("scan", text)

    def show_plan(self, plan: Any) -> None:
        self._record("plan", plan)

    def show_progress(self, progress: Any) -> None:
        self._record("progress", progress)

    def show_result(self, result: Any) -> None:
        self._record("result", result)

    def show_message(self, text: str) -> None:
        self._record("message", text)

    def show_welcome(self, steps: Any) -> None:
        self._record("welcome", steps)

    def forget_work(self) -> None:
        self._record("forget", None)

    def apply_theme(self, theme: str) -> None:
        self._record("theme", theme)

    def apply_language(self, catalog: Catalog) -> None:
        self._record("language", catalog.language)


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def make(
    backend: FakeBackend | None = None, *, threaded: bool = False, theme: str = "dark"
) -> tuple[Presenter, FakeView, FakeBackend, Clock]:
    view, fake, clock = FakeView(), backend or FakeBackend(), Clock()
    spawn: Callable[[Callable[[], None]], None] | None = None if threaded else (lambda work: work())
    presenter = Presenter(view, fake, clock=clock, detect_theme=lambda: theme, spawn=spawn)
    presenter.start()
    view.drain()
    return presenter, view, fake, clock


def converted(backend: FakeBackend | None = None) -> tuple[Presenter, FakeView, FakeBackend, Clock]:
    presenter, view, fake, clock = make(backend)
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    presenter.confirm()
    view.drain()
    return presenter, view, fake, clock


# --- States and actions (AC-01) ------------------------------------------------------------------


def test_it_starts_ready_with_convert_disabled_until_there_are_inputs() -> None:
    presenter, view, _, _ = make()
    state = view.last("state")
    assert state.state is AppState.READY and state.label == "Ready"
    assert not {Action.CONVERT, Action.REMOVE, Action.CANCEL} & state.enabled
    assert {Action.ADD, Action.HELP, Action.SETTINGS} <= state.enabled
    presenter.add_paths([Path("/docs/a.pdf")])
    assert {Action.CONVERT, Action.REMOVE} <= view.last("state").enabled


def test_each_state_enables_only_its_actions() -> None:
    presenter, view, fake, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    analyzing = view.last("state")
    assert analyzing.state is AppState.ANALYZING
    assert analyzing.enabled == {Action.CANCEL, Action.HELP}
    view.drain()
    waiting = view.last("state")
    assert waiting.state is AppState.WAITING_DECISION
    editing = {Action.ADD, Action.REMOVE, Action.CHOOSE_OUTPUT, Action.SETTINGS}
    assert waiting.enabled == {Action.CONFIRM, Action.BACK, Action.HELP} | editing  # ADR-0029


def test_the_seven_states_have_their_labels_in_both_languages() -> None:
    from clearmd.i18n import load_catalog

    for language in ("en", "es"):
        catalog = load_catalog(language)
        labels = {catalog.text(f"gui.state.{state.value}") for state in AppState}
        assert len(labels) == 7


# --- Inputs and the output choice (AC-05, AC-06) -------------------------------------------------


def test_inputs_are_never_listed_twice_and_can_be_removed() -> None:
    presenter, view, _, _ = make()
    presenter.add_paths([Path("/docs/a.pdf"), Path("/docs/a.pdf"), Path("/docs/../docs/a.pdf")])
    presenter.add_paths([Path("/docs/b")])
    rows = view.last("inputs")
    assert [row.path for row in rows] == [absolute("/docs/a.pdf"), absolute("/docs/b")]
    presenter.remove_input(Path("/docs/a.pdf"))
    assert [row.path for row in view.last("inputs")] == [absolute("/docs/b")]
    presenter.clear_inputs()
    assert view.last("inputs") == ()
    assert Action.CONVERT not in view.last("state").enabled


def test_the_output_goes_next_to_the_originals_by_default() -> None:
    presenter, view, fake, _ = make()
    assert view.last("output").mode is OutputMode.NEXT_TO
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    assert fake.plan_calls[-1]["output_root"] is None


def test_a_picked_folder_is_used_and_remembered(tmp_path: Path) -> None:
    presenter, view, fake, _ = make()
    presenter.choose_output_folder(tmp_path)
    choice = view.last("output")
    assert choice.mode is OutputMode.FOLDER and choice.folder == tmp_path
    assert fake.saved[-1].last_output_folder == str(tmp_path)
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    assert fake.plan_calls[-1]["output_root"] == tmp_path
    # Next time: still next to the originals by default, the folder offered as the suggestion.
    _, again, _, _ = make(FakeBackend(settings=fake.settings))
    assert again.last("output").mode is OutputMode.NEXT_TO
    assert again.last("output").suggestion == tmp_path


def test_the_settings_reach_the_plan() -> None:
    settings = Settings(recursive=False, html_strategy="article")
    presenter, _, fake, _ = make(FakeBackend(settings=settings))
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    call = fake.plan_calls[-1]
    assert call["recursive"] is False and call["html_strategy"] is Strategy.ARTICLE


# --- The plan (AC-07, AC-08) ---------------------------------------------------------------------


def test_the_plan_is_shown_and_nothing_runs_before_confirming() -> None:
    plan = BatchPlan(
        (planned("a.pdf"), planned("b.pdf", exists=True)),
        (SkippedItem(Path("/docs/notes.md"), SkipReason.ALREADY_MARKDOWN),),
        (),
    )
    presenter, view, fake, _ = make(FakeBackend(plan=plan))
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    shown = view.last("plan")
    assert fake.run_calls == []
    assert shown.summary == "To convert: 2 · Skipped: 1 · Already exist: 1"
    kinds = [row.kind for row in shown.rows]
    assert kinds == [RowKind.CONVERT, RowKind.EXISTS, RowKind.SKIPPED]
    skipped = shown.rows[-1]
    assert skipped.name == "notes.md"
    assert skipped.detail == "already Markdown. It needs no conversion."
    assert shown.asks_about_existing  # the setting is "ask"


def test_the_plan_gives_its_counts_as_figures_for_the_summary_cards() -> None:
    plan = BatchPlan(
        (planned("a.pdf"), planned("b.pdf", exists=True)),
        (SkippedItem(Path("/docs/notes.md"), SkipReason.ALREADY_MARKDOWN),),
        (),
    )
    presenter, view, _, _ = make(FakeBackend(plan=plan))
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    assert view.last("plan").stats == (
        Stat("To convert", 2, Tone.ACCENT),
        Stat("Skipped", 1, Tone.WARNING),
        Stat("Already exist", 1, Tone.NEUTRAL),
    )


@pytest.mark.parametrize(("setting", "overwrites"), [("overwrite", True), ("skip", False)])
def test_overwrite_and_skip_settings_never_ask(setting: str, overwrites: bool) -> None:
    plan = BatchPlan((planned("b.pdf", exists=True),), (), ())
    presenter, view, fake, _ = make(
        FakeBackend(plan=plan, settings=Settings(on_existing_output=setting))
    )
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    assert not view.last("plan").asks_about_existing
    presenter.confirm()
    view.drain()
    assert fake.run_calls[-1]["overwrite"](plan.conversions[0]) is overwrites


def test_with_ask_the_users_answer_decides() -> None:
    plan = BatchPlan((planned("b.pdf", exists=True),), (), ())
    presenter, view, fake, _ = make(FakeBackend(plan=plan))
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    presenter.confirm(overwrite=False)
    view.drain()
    assert fake.run_calls[-1]["overwrite"](plan.conversions[0]) is False


def test_a_plan_with_nothing_to_convert_cannot_be_confirmed() -> None:
    plan = BatchPlan((), (SkippedItem(Path("/docs/x.md"), SkipReason.ALREADY_MARKDOWN),), ())
    presenter, view, _, _ = make(FakeBackend(plan=plan))
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    assert Action.CONFIRM not in view.last("state").enabled
    assert view.last("plan").summary == "To convert: 0 · Skipped: 1 · Already exist: 0"


def test_back_from_the_plan_keeps_the_inputs() -> None:
    presenter, view, _, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    presenter.back()
    assert view.last("state").state is AppState.READY
    assert [row.path for row in view.last("inputs")] == [absolute("/docs")]


# --- Converting (AC-09, AC-10) -------------------------------------------------------------------


def test_progress_says_where_it_is_and_the_time_left_in_plain_words() -> None:
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf")), (), ())
    presenter, view, _, _ = converted(FakeBackend(plan=plan))
    progress = [value for call, value in view.calls if call == "progress"]
    assert progress[0].counter == "1 of 2" and progress[0].name == "a.pdf"
    assert progress[0].icon == "pdf"
    assert progress[0].time_left == "about 2 min left"
    assert progress[1].counter == "2 of 2" and progress[1].fraction == pytest.approx(0.5)


def test_a_file_that_takes_long_shows_a_timer_and_a_reassurance() -> None:
    gate = threading.Event()
    progress_seen: list[Any] = []
    fake = FakeBackend()
    presenter, view, _, clock = make(fake)
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()

    def slow() -> None:  # the file is still converting: the UI loop ticks the timer
        view.drain()
        clock.now += 25
        view.drain(timers=True)
        progress_seen.append(view.last("progress"))
        gate.set()

    fake.before_finish = slow
    presenter.confirm()
    view.drain()
    assert gate.is_set()
    shown = progress_seen[-1]
    assert shown.elapsed == "0:25" and shown.long_file == "Large files can take a few minutes."


def test_cancel_stops_at_once_and_ends_cancelled() -> None:
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf")), (), ())
    fake = FakeBackend(plan=plan)
    presenter, view, _, _ = make(fake)
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    fake.before_finish = presenter.cancel  # pressed while the first file converts
    presenter.confirm()
    view.drain()
    assert fake.run_calls[-1]["cancel"].is_set()
    assert view.last("state").state is AppState.CANCELLED
    assert fake.opened == []  # a cancelled batch never opens the folder by itself


def test_cancel_while_analyzing_discards_the_plan() -> None:
    presenter, view, fake, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    presenter.cancel()
    view.drain()
    assert view.last("state").state is AppState.READY
    assert not [call for call, _ in view.calls if call == "plan"]


# --- The result (AC-11, AC-12) -------------------------------------------------------------------


def test_a_clean_batch_finishes_and_opens_the_folder() -> None:
    presenter, view, fake, _ = converted()
    result = view.last("result")
    assert view.last("state").state is AppState.FINISHED
    assert result.counts == "1 converted · 0 skipped · 0 failed"
    assert fake.opened == [Path("/docs/ClearMD_Output")]
    assert Action.OPEN_RESULTS in view.last("state").enabled
    presenter.open_results()
    assert fake.opened == [Path("/docs/ClearMD_Output")] * 2


def test_the_folder_does_not_open_when_the_setting_says_no() -> None:
    _, _, fake, _ = converted(FakeBackend(settings=Settings(open_output_when_done=False)))
    assert fake.opened == []


def test_failures_never_stop_the_batch_and_say_what_to_do() -> None:
    plan = BatchPlan((planned("a.pdf"), planned("b.pdf"), planned("c.pdf")), (), ())
    statuses = {"a.pdf": OutcomeStatus.FAILED, "b.pdf": OutcomeStatus.STOPPED}
    _, view, fake, _ = converted(FakeBackend(plan=plan, statuses=statuses))
    assert len(fake.run_calls) == 1
    result = view.last("result")
    assert view.last("state").state is AppState.FINISHED_WITH_PROBLEMS
    assert result.counts == "1 converted · 0 skipped · 1 failed · 1 stopped"
    details = {row.name: row.detail for row in result.rows}
    assert details["a.pdf"] == "This file is password-protected. Remove the password and try again."
    assert details["b.pdf"].startswith("Exceeded the time limit (10 min).")
    assert result.stats == (
        Stat("Converted", 1, Tone.ACCENT),
        Stat("Skipped", 0, Tone.NEUTRAL),
        Stat("Failed", 1, Tone.DANGER),
        Stat("Stopped", 1, Tone.WARNING),
    )


# --- Threads (AC-02) -----------------------------------------------------------------------------


def test_the_work_runs_off_the_ui_thread_and_updates_come_back_to_it() -> None:
    presenter, view, fake, _ = make(threaded=True)
    worker_threads: list[int] = []
    real_plan = fake.plan_batch

    def plan_batch(inputs: Sequence[Path], **kwargs: Any) -> BatchPlan:
        worker_threads.append(threading.get_ident())
        return real_plan(inputs, **kwargs)

    fake.plan_batch = plan_batch  # type: ignore[method-assign]
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    for _ in range(200):  # the UI loop
        view.drain()
        if view.last("state").state is AppState.WAITING_DECISION:
            break
        threading.Event().wait(0.01)
    assert view.last("state").state is AppState.WAITING_DECISION
    assert worker_threads and worker_threads[0] != threading.get_ident()
    assert set(view.threads) == {threading.get_ident()}


def test_an_unexpected_error_in_the_work_is_told_and_the_app_goes_on() -> None:
    presenter, view, _, _ = make(FakeBackend(plan_error=RuntimeError("boom")))
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    assert view.last("state").state is AppState.READY
    assert "Something unexpected went wrong" in view.last("message")


# --- Language, settings, welcome (AC-03, AC-14, AC-15, AC-16) ------------------------------------


def test_texts_follow_the_language_setting() -> None:
    plan = BatchPlan((), (SkippedItem(Path("/docs/x.md"), SkipReason.ALREADY_MARKDOWN),), ())
    presenter, view, _, _ = make(FakeBackend(plan=plan, settings=Settings(language="es")))
    assert view.last("state").label == "Listo"
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    assert view.last("plan").rows[0].detail == "ya es Markdown. No necesita conversión."


def test_saving_settings_applies_the_language_and_the_theme() -> None:
    presenter, view, fake, _ = make(theme="dark")
    assert view.last("theme") == "dark"  # "system" follows the system
    presenter.save_settings(replace(fake.settings, language="es", theme="light"))
    assert fake.saved[-1].language == "es"
    assert view.last("language") == "es" and view.last("theme") == "light"
    assert view.last("state").label == "Listo"


def test_a_settings_file_that_cannot_be_written_is_told() -> None:
    presenter, view, fake, _ = make(FakeBackend(save_error=PermissionError("read-only")))
    presenter.save_settings(replace(fake.settings, theme="dark"))
    assert (
        view.last("message")
        == "ClearMD could not save the settings. Your changes apply until you close it."
    )


def test_restore_defaults_saves_the_defaults() -> None:
    presenter, _, fake, _ = make(FakeBackend(settings=Settings(language="es", recursive=False)))
    presenter.restore_defaults()
    assert fake.saved[-1] == Settings()


def test_the_welcome_shows_once_until_dismissed() -> None:
    _, view, fake, _ = make()
    steps = view.last("welcome")
    assert steps == (
        "1. Choose files or a folder",
        "2. Review what will be converted",
        "3. Done, your folder opens",
    )
    presenter, _, _, _ = make(fake)
    presenter.dismiss_welcome(show_again=False)
    assert fake.saved[-1].show_welcome is False
    _, again, _, _ = make(FakeBackend(settings=fake.settings))
    assert not [call for call, _ in again.calls if call == "welcome"]


def test_settings_problems_at_start_are_told_in_plain_words() -> None:
    warnings = (SettingsWarning("colour", SettingsProblem.UNKNOWN_KEY),)
    _, view, _, _ = make(FakeBackend(warnings=warnings))
    assert "colour" in view.last("message")


def test_rows_carry_their_file_icon_and_the_state_its_step(tmp_path: Path) -> None:
    (tmp_path / "a.pdf").write_bytes(b"%PDF")
    presenter, view, _, _ = make()
    assert view.last("state").step == 1
    presenter.add_paths([tmp_path / "a.pdf", tmp_path])
    assert [row.icon for row in view.last("inputs")] == ["pdf", "folder"]
    presenter.analyze()
    view.drain()
    assert view.last("state").step == 2
    assert all(row.icon for row in view.last("plan").rows)
    presenter.confirm()
    view.drain()
    assert view.last("state").step == 4


# --- Review of 005 (code review C-*, security audit S-*) -----------------------------------------


def calls_after(view: FakeView, name: str) -> list[str]:
    """The calls made after the last ``name`` call."""
    index = max(i for i, (call, _) in enumerate(view.calls) if call == name)
    return [call for call, _ in view.calls[index + 1 :]]


def test_c2_an_unexpected_error_is_told_after_the_state_changes() -> None:
    presenter, view, _, _ = make(FakeBackend(plan_error=RuntimeError("boom")))
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    assert "state" not in calls_after(view, "message")  # a step change would wipe it in a view
    message = view.last("message")
    assert "what was already converted is kept" in message  # C-13: true after a partial batch


def test_c3_start_up_warnings_come_after_the_first_state_in_one_message() -> None:
    warnings = (
        SettingsWarning("colour", SettingsProblem.UNKNOWN_KEY),
        SettingsWarning("theme", SettingsProblem.INVALID_VALUE),
    )
    _, view, _, _ = make(FakeBackend(warnings=warnings))
    assert "state" not in calls_after(view, "message")
    shown = view.last("message")
    assert "colour" in shown and "theme" in shown


def held() -> tuple[Presenter, FakeView, FakeBackend, list[Callable[[], None]]]:
    """A presenter whose work never runs until released: it stays ANALYZING or CONVERTING."""
    view, fake = FakeView(), FakeBackend()
    waiting: list[Callable[[], None]] = []
    presenter = Presenter(view, fake, detect_theme=lambda: "light", spawn=waiting.append)
    presenter.start()
    view.drain()
    return presenter, view, fake, waiting


def test_c4_inputs_and_the_output_cannot_change_while_analyzing() -> None:
    presenter, view, _, _ = held()
    presenter.add_paths([Path("/docs/a.pdf"), Path("/docs/b.pdf")])
    presenter.analyze()
    assert presenter.state is AppState.ANALYZING
    presenter.remove_input(Path("/docs/a.pdf"))
    presenter.clear_inputs()
    presenter.add_paths([Path("/docs/c.pdf")])
    presenter.choose_output_folder(Path("/elsewhere"))
    assert [row.name for row in view.last("inputs")] == ["a.pdf", "b.pdf"]
    assert presenter.output_folder is None


def test_c5_the_result_follows_a_language_change() -> None:
    presenter, view, fake, _ = converted()
    presenter.save_settings(replace(fake.settings, language="es"))
    assert view.last("result").stats[0].label == "Convertidos"


def test_c5_the_theme_is_applied_only_when_it_changes() -> None:
    presenter, view, fake, _ = make()
    themes = len([call for call, _ in view.calls if call == "theme"])
    presenter.save_settings(replace(fake.settings, language="es"))
    assert len([call for call, _ in view.calls if call == "theme"]) == themes


def test_c6_scan_progress_reaches_the_view_at_most_every_100_ms() -> None:
    from clearmd.backend.schemas.events import ScanProgress

    class Scanning(FakeBackend):
        def plan_batch(self, inputs: Sequence[Path], **kwargs: Any) -> BatchPlan:
            for found in range(500):
                kwargs["on_event"](ScanProgress(found=found, current=Path("/docs")))
            return super().plan_batch(inputs, **kwargs)

    presenter, view, _, _ = make(Scanning())
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain(timers=True)
    view.drain()
    scans = [value for call, value in view.calls if call == "scan"]
    assert len(scans) <= 3  # started, and the latest count once


def test_c8_cancelling_an_analysis_stops_the_scan() -> None:
    presenter, _, fake, waiting = held()
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    presenter.cancel()
    waiting.pop()()  # the worker runs now: its token was cancelled
    assert fake.plan_calls[-1]["cancel"].is_set()


def test_c12_every_folder_that_cannot_be_opened_is_told_in_one_message() -> None:
    class Unopenable(FakeBackend):
        def open_folder(self, path: Path) -> None:
            raise OSError("no file browser")

    plan = BatchPlan((planned("a.pdf"), planned("b.pdf", folder=Path("/other"))), (), ())
    presenter, view, _, _ = converted(Unopenable(plan=plan))
    presenter.open_results()
    shown = view.last("message")
    assert (
        str(Path("/docs/ClearMD_Output")) in shown and str(Path("/other/ClearMD_Output")) in shown
    )


def test_s1_a_folder_that_cannot_be_remembered_is_used_but_not_saved() -> None:
    presenter, _, fake, _ = make()
    odd = Path("/tmp/a\nb")
    presenter.choose_output_folder(odd)
    assert presenter.output_folder == absolute(str(odd))  # the results still go there
    assert all("\n" not in saved.last_output_folder for saved in fake.saved)
    presenter.save_settings(replace(presenter.settings, language="es"))
    assert fake.saved[-1].language == "es"  # later saves are not blocked


def test_s2_names_are_shown_with_invisible_characters_escaped() -> None:
    presenter, view, _, _ = make()
    presenter.add_paths([Path("/docs/x‮gpj.exe"), Path("/docs/a\nb.pdf")])
    names = [row.name for row in view.last("inputs")]
    assert names == ["x\\u202egpj.exe", "a\\nb.pdf"] or all(
        "‮" not in name and "\n" not in name for name in names
    )


# --- Adversarial verification of the fixes (A-*) -------------------------------------------------


def test_a1_a_window_closing_never_opens_the_results_afterwards() -> None:
    fake = FakeBackend(settings=Settings(open_output_when_done=True))
    presenter, view, _, _ = make(fake)
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    view.drain()
    presenter.shutdown()  # the window is closing: the batch may still finish normally
    presenter.confirm()
    view.drain()
    assert view.last("state").state is AppState.FINISHED
    assert fake.opened == []


def test_a2_a_cancelled_analysis_never_swallows_the_next_ones_count() -> None:
    presenter, view, _, _ = held()
    presenter.add_paths([Path("/docs")])
    presenter.analyze()
    presenter._scanned(presenter._generation, 7)  # a count arrives: its timer is pending
    presenter.cancel()
    presenter.analyze()
    presenter._scanned(presenter._generation, 1234)  # the new analysis's count
    for _ in range(3):
        view.drain(timers=True)  # the old timer fires first
    scans = [value for call, value in view.calls if call == "scan"]
    assert any("1234" in text for text in scans)


# --- Pages and their primary action (feature 007, ADR-0029) --------------------------------------


def state(view: FakeView) -> Any:
    return view.last("state")


def test_every_page_can_be_opened_at_any_time_and_only_the_page_changes() -> None:
    presenter, view, _, _ = make()
    for page in (4, 2, 3, 1):
        presenter.go_to(page)
        assert state(view).page == page
        assert state(view).state is AppState.READY


def test_choose_says_next_and_why_it_is_disabled_without_inputs() -> None:
    presenter, view, _, _ = make()
    primary = state(view).primary
    assert (primary.label, primary.enabled) == ("Next", False)
    assert primary.hint == "Add at least one file or folder."
    presenter.add_paths([Path("/docs/a.pdf")])
    primary = state(view).primary
    assert primary.enabled and primary.hint == ""


def test_next_plans_and_opens_review_then_next_opens_convert() -> None:
    presenter, view, fake, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.press_primary()
    view.drain()
    assert state(view).page == 2 and state(view).state is AppState.WAITING_DECISION
    assert state(view).primary.label == "Next"
    presenter.press_primary()
    assert state(view).page == 3 and fake.run_calls == []  # nothing runs before Convert
    assert state(view).primary.label == "Convert" and state(view).primary.enabled


def test_convert_runs_on_its_page_and_results_open_at_the_end() -> None:
    presenter, view, fake, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.press_primary()
    view.drain()
    presenter.go_to(3)
    presenter.press_primary()
    pages = [value.page for call, value in view.calls if call == "state"]
    view.drain()
    assert 3 in pages and state(view).page == 4
    assert state(view).primary.label == "Open results folder"
    assert fake.run_calls


def test_review_and_convert_explain_what_is_missing() -> None:
    presenter, view, _, _ = make()
    presenter.add_paths([Path("/docs")])  # chosen, not planned yet
    presenter.go_to(2)
    assert state(view).primary.hint == "Press Next on Choose to see what will happen."
    presenter.go_to(3)
    assert not state(view).primary.enabled
    assert state(view).primary.hint == "Press Next on Choose to see what will happen."
    presenter.go_to(4)
    assert state(view).primary.hint == "Convert something first: the results appear here."


def test_a_plan_with_nothing_to_convert_says_so() -> None:
    plan = BatchPlan((), (), ())
    presenter, view, _, _ = make(FakeBackend(plan=plan))
    presenter.add_paths([Path("/docs")])
    presenter.press_primary()
    view.drain()
    assert not state(view).primary.enabled
    assert state(view).primary.hint == "Nothing here can be converted. Go back to Choose."


def test_changing_the_inputs_after_a_plan_drops_it() -> None:
    presenter, view, _, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.press_primary()
    view.drain()
    presenter.go_to(1)
    presenter.add_paths([Path("/more")])
    assert state(view).state is AppState.READY
    presenter.go_to(2)
    assert not state(view).primary.enabled  # press Next on Choose again


def test_nothing_can_be_edited_while_converting() -> None:
    view, fake = FakeView(), FakeBackend()
    waiting: list[Callable[[], None]] = []
    presenter = Presenter(view, fake, detect_theme=lambda: "light", spawn=waiting.append)
    presenter.start()
    presenter.add_paths([Path("/docs")])
    presenter.press_primary()
    waiting.pop()()
    view.drain()
    presenter.go_to(3)
    presenter.press_primary()
    assert presenter.state is AppState.CONVERTING
    presenter.go_to(1)
    presenter.clear_inputs()
    assert [row.name for row in view.last("inputs")] == ["docs"]
    assert state(view).primary.hint == "Converting… wait for it to finish, or cancel it."


def test_convert_more_keeps_or_clears_the_inputs() -> None:
    plan = BatchPlan((planned("a.pdf"),), (), ())
    for keep, expected in ((True, ["docs"]), (False, [])):
        presenter, view, _, _ = make(FakeBackend(plan=plan))
        presenter.add_paths([Path("/docs")])
        presenter.press_primary()
        view.drain()
        presenter.go_to(3)
        presenter.press_primary()
        view.drain()
        presenter.convert_more(keep=keep)
        assert state(view).page == 1 and state(view).state is AppState.READY
        assert [row.name for row in view.last("inputs")] == expected


def test_the_version_is_known() -> None:
    presenter, _, _, _ = make()
    assert presenter.version[0].isdigit()


# --- Security audit of 007 (F-*, N-*, I-*) -------------------------------------------------------


def test_n1_next_on_choose_after_a_batch_starts_a_new_plan() -> None:
    presenter, view, fake, _ = converted()
    presenter.go_to(1)
    presenter.press_primary()
    view.drain()
    assert len(fake.plan_calls) == 2 and state(view).page == 2


def test_f2_each_plan_has_its_own_id() -> None:
    presenter, view, _, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.press_primary()
    view.drain()
    first = view.last("plan").plan_id
    presenter.go_to(1)
    presenter.add_paths([Path("/more")])
    presenter.remove_input(Path("/more"))
    presenter.press_primary()
    view.drain()
    assert view.last("plan").plan_id != first  # same rows, another plan: the answer resets


def test_i1_a_setting_that_changes_the_plan_drops_it() -> None:
    presenter, view, fake, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.press_primary()
    view.drain()
    presenter.save_settings(replace(presenter.settings, language="es"))
    assert state(view).state is AppState.WAITING_DECISION  # the language changes no plan
    presenter.save_settings(replace(presenter.settings, recursive=False))
    assert state(view).state is AppState.READY


# --- Code review of 007 (C7-*) -------------------------------------------------------------------


def test_c7_1_an_edit_that_drops_the_plan_tells_the_view() -> None:
    presenter, view, _, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.press_primary()
    view.drain()
    presenter.add_paths([Path("/more")])
    assert "forget" in [call for call, _ in view.calls]


def test_c7_3_many_inputs_are_removed_at_once() -> None:
    presenter, view, _, _ = make()
    presenter.add_paths([Path(f"/docs/{n}.pdf") for n in range(50)])
    before = len(view.calls)
    presenter.remove_inputs([Path(f"/docs/{n}.pdf") for n in range(49)])
    assert [row.name for row in view.last("inputs")] == ["49.pdf"]
    assert len([call for call, _ in view.calls[before:] if call == "inputs"]) == 1


def test_c7_4_an_edit_that_changes_nothing_keeps_the_plan() -> None:
    presenter, view, _, _ = make()
    presenter.add_paths([Path("/docs")])
    presenter.press_primary()
    view.drain()
    presenter.add_paths([Path("/docs")])  # already listed
    presenter.remove_input(Path("/not-listed"))
    presenter.choose_output_next_to()  # already next to the originals
    assert state(view).state is AppState.WAITING_DECISION


# --- Feature 009: the summary's format ---------------------------------------------------------


def test_the_summary_format_is_chosen_remembered_and_sent_to_the_batch() -> None:
    presenter, view, fake, _ = make()
    assert view.last("output").summary_format == "markdown"
    presenter.choose_summary_format("markdown_pdf")
    assert fake.settings.summary_format == "markdown_pdf"
    assert view.last("output").summary_format == "markdown_pdf"
    presenter.choose_summary_format("docx")  # not a format: nothing changes
    assert fake.settings.summary_format == "markdown_pdf"
    presenter.add_paths([Path("/docs")])
    presenter.press_primary()
    view.drain()
    presenter.go_to(3)
    presenter.press_primary(False)
    view.drain()
    assert fake.run_calls[-1]["summary_pdf"] is True


# --- Feature 011: the hint says what is missing on every page ----------------------------------


def test_with_nothing_chosen_every_page_says_to_choose_first() -> None:
    presenter, view, _, _ = make()
    for page in (2, 3, 4):
        presenter.go_to(page)
        assert state(view).primary.hint == "Nothing chosen yet: add files or folders on Choose."
    presenter.add_paths([Path("/docs")])
    presenter.go_to(2)
    assert state(view).primary.hint == "Press Next on Choose to see what will happen."
