"""The presenter: the state, the intents and every text, once for every GUI (ADR-0026).

The view is passive (``ports.View``). Planning and converting run off the UI thread (``spawn``);
their events come back through ``view.after(0, …)``, so the presenter only changes on the UI
thread. Each piece of work carries a generation: what a cancelled analysis returns later is
dropped.
"""

import os
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import replace
from functools import partial
from pathlib import Path

from clearmd.backend.api import (
    CancelToken,
    Strategy,
    skip_action,
    skip_reason,
    stopped_message,
)
from clearmd.backend.schemas.events import (
    BatchEvent,
    ConversionFinished,
    ConversionStarted,
    ScanProgress,
)
from clearmd.backend.schemas.models import (
    BatchPlan,
    BatchReport,
    OutcomeStatus,
    PlannedConversion,
)
from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.presenter.icons import FOLDER, icon_for, icon_of_format
from clearmd.frontend.presenter.models import (
    InputRow,
    OutputChoice,
    OutputMode,
    PlanRow,
    PlanView,
    ProgressView,
    ResultRow,
    ResultView,
    RowKind,
    StateView,
)
from clearmd.frontend.presenter.ports import ApiBackend, Backend, View
from clearmd.frontend.presenter.state import AppState, enabled_actions, step_of
from clearmd.frontend.presenter.system_theme import detect_system_theme
from clearmd.i18n import Catalog, load_catalog, printable, resolve_language

LONG_FILE_SECONDS = 15  # after this, the file's timer and "large files can take a few minutes"
TICK_MILLISECONDS = 1000


def _in_background(work: Callable[[], None]) -> None:
    threading.Thread(target=work, name="clearmd-work", daemon=True).start()


class Presenter:
    def __init__(
        self,
        view: View,
        backend: Backend | None = None,
        *,
        clock: Callable[[], float] = time.monotonic,
        detect_theme: Callable[[], str] = detect_system_theme,
        spawn: Callable[[Callable[[], None]], None] | None = None,
    ) -> None:
        self._view = view
        self._backend = backend or ApiBackend()
        self._clock = clock
        self._detect_theme = detect_theme
        self._spawn = spawn or _in_background
        self.settings = Settings()
        self.catalog: Catalog = load_catalog("en")
        self.state = AppState.READY
        self._inputs: list[Path] = []
        self._output_folder: Path | None = None
        self._plan: BatchPlan | None = None
        self._report: BatchReport | None = None
        self._cancel: CancelToken | None = None
        self._generation = 0
        self._current: tuple[int, int, str, float | None] | None = None  # index, total, name, left
        self._started_at = 0.0
        self._done = 0

    # --- Start -----------------------------------------------------------------------------------

    def start(self) -> None:
        """Read the settings, apply the language and the theme, show the welcome if wanted."""
        settings, warnings = self._backend.load_settings()
        self._apply(settings)
        for warning in warnings:
            text = self.catalog.text(f"settings.{warning.problem.value}", setting=warning.key)
            self._view.show_message(printable(text))
        self._show_inputs()
        self._show_output()
        self._set(AppState.READY)
        if self.settings.show_welcome:
            self._view.show_welcome(
                tuple(self.catalog.text(f"gui.welcome.step{n}") for n in (1, 2, 3))
            )

    def _apply(self, settings: Settings) -> None:
        self.settings = settings
        self.catalog = load_catalog(resolve_language(None, settings.language))
        self._view.apply_language(self.catalog)
        theme = settings.theme if settings.theme != "system" else self._detect_theme()
        self._view.apply_theme(theme if theme in {"light", "dark"} else "light")

    @property
    def output_folder(self) -> Path | None:
        """The folder chosen for the results; ``None``: next to the originals."""
        return self._output_folder

    # --- Inputs and the output -------------------------------------------------------------------

    def add_paths(self, paths: Sequence[Path]) -> None:
        """Files or folders, from the dialogs or dropped on the window; never listed twice."""
        known = {_key(path) for path in self._inputs}
        for path in paths:
            absolute = Path(os.path.abspath(path))
            if _key(absolute) not in known:
                known.add(_key(absolute))
                self._inputs.append(absolute)
        self._show_inputs()
        self._set(self.state)

    def remove_input(self, path: Path) -> None:
        self._inputs = [known for known in self._inputs if _key(known) != _key(Path(path))]
        self._show_inputs()
        self._set(self.state)

    def clear_inputs(self) -> None:
        self._inputs.clear()
        self._show_inputs()
        self._set(self.state)

    def choose_output_next_to(self) -> None:
        self._output_folder = None
        self._show_output()

    def choose_output_folder(self, folder: Path) -> None:
        """Results in ``folder``, remembered as the suggestion for next time (ADR-0016)."""
        self._output_folder = Path(os.path.abspath(folder))
        self._show_output()
        self._save(replace(self.settings, last_output_folder=str(self._output_folder)))

    # --- Plan, confirm, convert ------------------------------------------------------------------

    def analyze(self) -> None:
        """Compute the plan (off the UI thread); nothing is written until the user confirms."""
        if self.state is not AppState.READY or not self._inputs:
            return
        generation = self._next_generation()
        inputs = list(self._inputs)
        options = {
            "recursive": self.settings.recursive,
            "output_root": self._output_folder,
            "html_strategy": Strategy(self.settings.html_strategy),
        }
        self._set(AppState.ANALYZING)
        self._view.show_scan(self.catalog.text("gui.scan.started"))

        def on_event(event: BatchEvent) -> None:
            if isinstance(event, ScanProgress):
                self._later(generation, lambda: self._scanned(event.found))

        def work() -> None:
            try:
                plan = self._backend.plan_batch(inputs, on_event=on_event, **options)
            except Exception as error:  # noqa: BLE001 -- told to the user, the app goes on
                self._later(generation, partial(self._unexpected, error))
                return
            self._later(generation, lambda: self._planned(plan))

        self._spawn(work)

    def confirm(self, overwrite: bool | None = None) -> None:
        """Convert the plan. ``overwrite`` answers the question about existing outputs."""
        if self.state is not AppState.WAITING_DECISION or not self._plan:
            return
        plan = self._plan
        if not plan.conversions:
            return
        choice = self.settings.on_existing_output
        overwrites = choice == "overwrite" if choice != "ask" else bool(overwrite)
        generation = self._next_generation()
        self._cancel = token = CancelToken()
        self._done = 0
        self._current = None
        self._set(AppState.CONVERTING)

        def on_event(event: BatchEvent) -> None:
            if isinstance(event, ConversionStarted):
                left, name = event.seconds_left, event.item.source.name
                self._later(generation, lambda: self._started(event.index, event.total, name, left))
            elif isinstance(event, ConversionFinished):
                self._later(generation, self._finished_one)

        def work() -> None:
            try:
                report = self._backend.run_batch(
                    plan,
                    overwrite=lambda item: overwrites,
                    on_event=on_event,
                    cancel=token,
                    language=self.catalog.language,
                )
            except Exception as error:  # noqa: BLE001 -- told to the user, the app goes on
                self._later(generation, partial(self._unexpected, error))
                return
            self._later(generation, lambda: self._converted(report))

        self._view.after(TICK_MILLISECONDS, lambda: self._tick(generation))  # this file's timer
        self._spawn(work)

    def cancel(self) -> None:
        """Stop now: an analysis is dropped; a batch stops its current file at once (ADR-0015)."""
        if self.state is AppState.ANALYZING:
            self._next_generation()  # whatever it returns is dropped
            self._set(AppState.READY)
        elif self.state is AppState.CONVERTING and self._cancel is not None:
            self._cancel.cancel()
            self._view.show_message(self.catalog.text("gui.progress.cancelling"))

    def back(self) -> None:
        """From the plan or the result, to the inputs again (they are kept)."""
        if self.state in {AppState.ANALYZING, AppState.CONVERTING}:
            return
        self._plan = None
        self._report = None
        self._set(AppState.READY)

    def open_results(self) -> None:
        for folder in self._result_folders():
            try:
                self._backend.open_folder(folder)
            except (OSError, ValueError):
                self._view.show_message(
                    self.catalog.text("gui.result.cannot_open", path=str(folder))
                )

    # --- Settings and welcome --------------------------------------------------------------------

    def save_settings(self, settings: Settings) -> None:
        """Save and apply at once (language, theme); told if the file cannot be written."""
        self._apply(settings)
        self._save(settings)
        self._show_inputs()
        self._show_output()
        self._set(self.state)

    def restore_defaults(self) -> None:
        self.save_settings(Settings())

    def dismiss_welcome(self, *, show_again: bool) -> None:
        if not show_again:
            self._save(replace(self.settings, show_welcome=False))

    def _save(self, settings: Settings) -> None:
        self.settings = settings
        try:
            self._backend.save_settings(settings)
        except (OSError, ValueError):
            self._view.show_message(self.catalog.text("gui.settings.not_saved"))

    # --- Work coming back (UI thread) ------------------------------------------------------------

    def _later(self, generation: int, callback: Callable[[], None]) -> None:
        """From the worker thread: run ``callback`` on the UI thread, unless it is stale."""

        def guarded() -> None:
            if generation == self._generation:
                callback()

        self._view.after(0, guarded)

    def _next_generation(self) -> int:
        self._generation += 1
        return self._generation

    def _scanned(self, found: int) -> None:
        self._view.show_scan(self.catalog.text("gui.scan.found", count=found))

    def _planned(self, plan: BatchPlan) -> None:
        self._plan = plan
        self._view.show_plan(self._plan_view(plan))
        self._set(AppState.WAITING_DECISION)

    def _started(self, index: int, total: int, name: str, left: float | None) -> None:
        self._current = (index, total, name, left)
        self._started_at = self._clock()
        self._show_progress()

    def _finished_one(self) -> None:
        self._done += 1

    def _tick(self, generation: int) -> None:
        if generation != self._generation or self.state is not AppState.CONVERTING:
            return
        self._show_progress()
        self._view.after(TICK_MILLISECONDS, lambda: self._tick(generation))

    def _converted(self, report: BatchReport) -> None:
        self._report = report
        self._cancel = None
        problems = any(
            outcome.status in {OutcomeStatus.FAILED, OutcomeStatus.STOPPED}
            for outcome in report.outcomes
        )
        state = (
            AppState.CANCELLED
            if report.cancelled
            else AppState.FINISHED_WITH_PROBLEMS
            if problems or report.unwritten_summaries
            else AppState.FINISHED
        )
        self._view.show_result(self._result_view(report, state))
        self._set(state)
        if state is not AppState.CANCELLED and self.settings.open_output_when_done:
            self.open_results()

    def _unexpected(self, error: Exception) -> None:
        detail = printable(f"{type(error).__name__}: {error}")
        self._view.show_message(self.catalog.text("cli.unexpected_error", detail=detail))
        self._cancel = None
        self._set(AppState.READY)

    # --- What the view draws ---------------------------------------------------------------------

    def _set(self, state: AppState) -> None:
        self.state = state
        plan = self._plan
        enabled = enabled_actions(
            state,
            has_inputs=bool(self._inputs),
            can_confirm=bool(plan and plan.conversions),
            has_results=bool(self._result_folders()),
        )
        label = self.catalog.text(f"gui.state.{state.value}")
        self._view.show_state(StateView(state, label, enabled, step_of(state)))

    def _show_inputs(self) -> None:
        rows = []
        for path in self._inputs:
            is_folder = path.is_dir()
            name = path.name or str(path)
            icon = icon_for(path, is_folder=is_folder)
            rows.append(InputRow(path, name, str(path.parent), is_folder, icon))
        self._view.show_inputs(tuple(rows))

    def _show_output(self) -> None:
        remembered = self.settings.last_output_folder
        suggestion = Path(remembered) if remembered else None
        if self._output_folder is None:
            label = self.catalog.text("gui.output.next_to_detail")
            choice = OutputChoice(OutputMode.NEXT_TO, None, suggestion, label)
        else:
            label = self.catalog.text("gui.output.folder", path=str(self._output_folder))
            choice = OutputChoice(OutputMode.FOLDER, self._output_folder, suggestion, label)
        self._view.show_output_choice(choice)

    def _show_progress(self) -> None:
        if self._current is None:
            return
        index, total, name, left = self._current
        elapsed = self._clock() - self._started_at
        long_file = elapsed >= LONG_FILE_SECONDS
        self._view.show_progress(
            ProgressView(
                counter=self.catalog.text("gui.progress.counter", index=index, total=total),
                name=name,
                fraction=self._done / total if total else 0.0,
                time_left=(
                    self.catalog.text("cli.time_left", duration=self.catalog.duration(left))
                    if left is not None
                    else None
                ),
                elapsed=self.catalog.clock(elapsed) if long_file else None,
                long_file=self.catalog.text("gui.progress.long_file") if long_file else None,
            )
        )

    def _plan_view(self, plan: BatchPlan) -> PlanView:
        rows: list[PlanRow] = []
        for item in plan.conversions:
            kind = RowKind.EXISTS if item.exists else RowKind.CONVERT
            icon = icon_of_format(item.detection.format)
            source = item.source
            rows.append(PlanRow(kind, source.name, str(source.parent), self._format(item), icon))
        for skipped in plan.skipped:
            reason = skip_reason(self.catalog, skipped)
            detail = f"{reason}. {skip_action(self.catalog, skipped)}"
            name = skipped.path.name + ("/" if skipped.is_dir else "")
            icon = icon_for(skipped.path, is_folder=skipped.is_dir)
            rows.append(PlanRow(RowKind.SKIPPED, name, str(skipped.path.parent), detail, icon))
        for missing in plan.input_errors:
            detail = self.catalog.text("gui.plan.not_found")
            path = missing.path
            icon = icon_for(path, is_folder=False)  # it is not there: its name is all we know
            rows.append(PlanRow(RowKind.MISSING, path.name, str(path.parent), detail, icon))
        existing = len(plan.existing)
        summary = self.catalog.text(
            "gui.plan.summary",
            convert=len(plan.conversions),
            skipped=len(plan.skipped) + len(plan.input_errors),
            existing=existing,
        )
        asks = existing > 0 and self.settings.on_existing_output == "ask"
        return PlanView(summary, tuple(rows), asks)

    def _format(self, item: PlannedConversion) -> str:
        shown = item.detection.format.value.upper()
        if item.strategy is not Strategy.FULL:
            shown = self.catalog.text(f"summary.strategy.{item.strategy.value}", format=shown)
        return shown

    def _result_view(self, report: BatchReport, state: AppState) -> ResultView:
        count = {status: 0 for status in OutcomeStatus}
        rows: list[ResultRow] = []
        for outcome in report.outcomes:
            count[outcome.status] += 1
            source = outcome.item.source
            if outcome.status is OutcomeStatus.FAILED and outcome.error is not None:
                detail = self.catalog.error(outcome.error)
            elif outcome.status is OutcomeStatus.STOPPED and outcome.error is not None:
                action = self.catalog.text(outcome.error.action_key)
                detail = f"{stopped_message(self.catalog, outcome)} {action}"
            elif outcome.status is OutcomeStatus.KEPT:
                detail = self.catalog.text("gui.result.kept")
            else:
                continue
            icon = icon_of_format(outcome.item.detection.format)
            rows.append(ResultRow(source.name, str(source.parent), detail, icon))
        for skipped in report.skipped:
            reason = skip_reason(self.catalog, skipped)
            detail = f"{reason}. {skip_action(self.catalog, skipped)}"
            icon = icon_for(skipped.path, is_folder=skipped.is_dir)
            rows.append(ResultRow(skipped.path.name, str(skipped.path.parent), detail, icon))
        for root in report.unwritten_summaries:
            detail = self.catalog.text("gui.result.no_summary")
            rows.append(ResultRow(root.name, str(root.parent), detail, FOLDER))
        counts = self.catalog.text(
            "cli.summary",
            converted=count[OutcomeStatus.CONVERTED],
            skipped=len(report.skipped) + count[OutcomeStatus.KEPT],
            failed=count[OutcomeStatus.FAILED],
        )
        if count[OutcomeStatus.STOPPED]:
            counts += self.catalog.text("cli.summary_stopped", stopped=count[OutcomeStatus.STOPPED])
        headline = self.catalog.text(f"gui.state.{state.value}")
        return ResultView(headline, counts, tuple(rows), self._result_folders(report))

    def _result_folders(self, report: BatchReport | None = None) -> tuple[Path, ...]:
        """The ClearMD_Output folders that hold converted files (none before a batch)."""
        report = report or self._report
        if report is None:
            return ()
        roots = dict.fromkeys(
            outcome.item.output_root
            for outcome in report.outcomes
            if outcome.status is OutcomeStatus.CONVERTED
        )
        return tuple(roots)


def _key(path: Path) -> str:
    """How two inputs are the same: the same absolute, normalized path."""
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))
