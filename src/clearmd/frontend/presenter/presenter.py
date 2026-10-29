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
from importlib.metadata import PackageNotFoundError, version
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
from clearmd.backend.schemas.settings import Settings, valid_path_setting
from clearmd.frontend.presenter.icons import FOLDER, icon_for, icon_of_format
from clearmd.frontend.presenter.models import (
    InputRow,
    OutputChoice,
    OutputMode,
    PlanRow,
    PlanView,
    Primary,
    ProgressView,
    ResultRow,
    ResultView,
    RowKind,
    Stat,
    StateView,
    Tone,
)
from clearmd.frontend.presenter.ports import ApiBackend, Backend, View
from clearmd.frontend.presenter.state import WORKING, AppState, enabled_actions, step_of
from clearmd.frontend.presenter.system_theme import detect_system_theme
from clearmd.i18n import Catalog, load_catalog, printable, resolve_language

SCAN_MS = 100  # the scan count is shown at most this often (code review of 005)
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
        detect_theme: Callable[[], str] | None = None,
        spawn: Callable[[Callable[[], None]], None] | None = None,
    ) -> None:
        self._view = view
        self._backend = backend or ApiBackend()
        self._clock = clock
        self._detect_theme = detect_theme or detect_system_theme
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
        # index, total, name, seconds left, icon
        self._current: tuple[int, int, str, float | None, str] | None = None
        self._started_at = 0.0
        self._done = 0
        self._theme: str | None = None
        self._shutting_down = False  # the window is closing: nothing is opened any more
        self._scan_count: tuple[int, int] | None = None  # (generation, latest count), SCAN_MS
        self.page = 1  # the step on screen (ADR-0029)

    # --- Start -----------------------------------------------------------------------------------

    def start(self) -> None:
        """Read the settings, apply the language and the theme, show the welcome if wanted."""
        settings, warnings = self._backend.load_settings()
        self._apply(settings)
        self._show_inputs()
        self._show_output()
        self._set(AppState.READY)
        if warnings:  # after the first state: a view may clear its message on a step change
            lines = (
                self.catalog.text(f"settings.{warning.problem.value}", setting=warning.key)
                for warning in warnings
            )
            self._view.show_message("\n".join(printable(line) for line in lines))
        if self.settings.show_welcome:
            self._view.show_welcome(
                tuple(self.catalog.text(f"gui.welcome.step{n}") for n in (1, 2, 3))
            )

    def _apply(self, settings: Settings) -> None:
        self.settings = settings
        self.catalog = load_catalog(resolve_language(None, settings.language))
        self._view.apply_language(self.catalog)
        theme = settings.theme if settings.theme != "system" else self._detect_theme()
        theme = theme if theme in {"light", "dark"} else "light"
        if theme != self._theme:  # redrawing the lists for nothing loses their selection
            self._theme = theme
            self._view.apply_theme(theme)

    @property
    def version(self) -> str:
        """ClearMD's version, as shown in the window and the help."""
        try:
            return version("clearmd")
        except PackageNotFoundError:  # running from sources without metadata
            return "dev"

    @property
    def output_folder(self) -> Path | None:
        """The folder chosen for the results; ``None``: next to the originals."""
        return self._output_folder

    # --- Inputs and the output -------------------------------------------------------------------

    def add_paths(self, paths: Sequence[Path]) -> None:
        """Files or folders, from the dialogs or dropped on the window; never listed twice."""
        if not self._editable():
            return
        known = {_key(path) for path in self._inputs}
        for path in paths:
            absolute = Path(os.path.abspath(path))
            if _key(absolute) not in known:
                known.add(_key(absolute))
                self._inputs.append(absolute)
        self._show_inputs()
        self._set(self.state)

    def remove_input(self, path: Path) -> None:
        if not self._editable():
            return
        self._inputs = [known for known in self._inputs if _key(known) != _key(Path(path))]
        self._show_inputs()
        self._set(self.state)

    def clear_inputs(self) -> None:
        if not self._editable():
            return
        self._inputs.clear()
        self._show_inputs()
        self._set(self.state)

    def choose_output_next_to(self) -> None:
        if not self._editable():
            return
        self._output_folder = None
        self._show_output()
        self._set(self.state)

    def choose_output_folder(self, folder: Path) -> None:
        """Results in ``folder``, remembered as the suggestion for next time (ADR-0016) when its
        path can be stored (a name with control characters still receives the results)."""
        if not self._editable():
            return
        self._output_folder = Path(os.path.abspath(folder))
        self._show_output()
        self._set(self.state)
        if valid_path_setting(str(self._output_folder)):
            self._save(replace(self.settings, last_output_folder=str(self._output_folder)))

    def _editable(self) -> bool:
        """Inputs and output change outside the work only; a change drops a plan or a result
        (it was made from the inputs as they were, ADR-0029)."""
        if self.state in WORKING:
            return False
        if self.state is not AppState.READY:
            self._plan = None
            self._report = None
            self.state = AppState.READY
        return True

    # --- Pages (ADR-0029) ------------------------------------------------------------------------

    def go_to(self, page: int) -> None:
        """Show a step; only what is on screen changes."""
        if 1 <= page <= 4:
            self.page = page
            self._set(self.state)

    def press_primary(self, overwrite: bool | None = None) -> None:
        """The page's primary action: Next, Next, Convert, Open results folder."""
        if not self._primary().enabled:
            return
        if self.page == 1:
            if self.state is AppState.WAITING_DECISION:
                self.go_to(2)
            else:
                self.analyze()
        elif self.page == 2:
            self.go_to(3)
        elif self.page == 3:
            self.confirm(overwrite)
        else:
            self.open_results()

    def convert_more(self, *, keep: bool) -> None:
        """From the results to Choose again, with the chosen files or without them."""
        if self.state in WORKING:
            return
        self._plan = None
        self._report = None
        if not keep:
            self._inputs.clear()
        self.page = 1
        self._show_inputs()
        self._set(AppState.READY)

    def _primary(self) -> Primary:
        text = self.catalog.text
        plan = self._plan
        ready = self.state is AppState.WAITING_DECISION and bool(plan and plan.conversions)

        def why() -> str:
            if self.state is AppState.ANALYZING:
                return text("gui.nav.analyzing")
            if self.state is AppState.CONVERTING:
                return text("gui.nav.converting")
            if self.state is AppState.WAITING_DECISION:
                return text("gui.nav.nothing")
            if self._report is not None:
                return text("gui.nav.done")
            return text("gui.nav.need_plan")

        if self.page == 1:
            if self.state in WORKING:
                return Primary(text("gui.nav.next"), False, why())
            if not self._inputs:
                return Primary(text("gui.nav.next"), False, text("gui.nav.need_inputs"))
            return Primary(text("gui.nav.next"), True)
        if self.page == 2:
            return Primary(text("gui.nav.next"), ready, "" if ready else why())
        if self.page == 3:
            return Primary(text("gui.main.convert"), ready, "" if ready else why())
        has_results = bool(self._result_folders())
        hint = "" if has_results else text("gui.nav.no_results")
        return Primary(text("gui.result.open"), has_results, hint)

    # --- Plan, confirm, convert ------------------------------------------------------------------

    def analyze(self) -> None:
        """Compute the plan (off the UI thread); nothing is written until the user confirms."""
        if self.state is not AppState.READY or not self._inputs:
            return
        generation = self._next_generation()
        inputs = list(self._inputs)
        self.page = 1  # the scan is told on Choose; Review opens with the plan
        options = {
            "recursive": self.settings.recursive,
            "output_root": self._output_folder,
            "html_strategy": Strategy(self.settings.html_strategy),
        }
        self._cancel = token = CancelToken()
        self._scan_count = None
        self._set(AppState.ANALYZING)
        self._view.show_scan(self.catalog.text("gui.scan.started"))

        def on_event(event: BatchEvent) -> None:
            if isinstance(event, ScanProgress):
                self._later(generation, lambda: self._scanned(generation, event.found))

        def work() -> None:
            try:
                plan = self._backend.plan_batch(inputs, on_event=on_event, cancel=token, **options)
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
        language = self.catalog.language  # read here: the worker never touches the presenter
        self._done = 0
        self._current = None
        self.page = 3  # the progress is shown on Convert (ADR-0029)
        self._set(AppState.CONVERTING)

        def on_event(event: BatchEvent) -> None:
            if isinstance(event, ConversionStarted):
                left, name = event.seconds_left, event.item.source.name
                icon = icon_of_format(event.item.detection.format)
                name = printable(name)
                self._later(
                    generation, lambda: self._started(event.index, event.total, name, left, icon)
                )
            elif isinstance(event, ConversionFinished):
                self._later(generation, self._finished_one)

        def work() -> None:
            try:
                report = self._backend.run_batch(
                    plan,
                    overwrite=lambda item: overwrites,
                    on_event=on_event,
                    cancel=token,
                    language=language,
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
            if self._cancel is not None:
                self._cancel.cancel()  # and the scan stops at its next folder
            self._cancel = None
            self.page = 1
            self._set(AppState.READY)
        elif self.state is AppState.CONVERTING and self._cancel is not None:
            self._cancel.cancel()
            self._view.show_message(self.catalog.text("gui.progress.cancelling"))

    def shutdown(self) -> None:
        """The window is closing: a batch may still end (its summary is written), but nothing
        opens afterwards (adversarial review of 005)."""
        self._shutting_down = True

    def back(self) -> None:
        """From the plan or the result, to the inputs again (they are kept)."""
        self.convert_more(keep=True)

    def open_results(self) -> None:
        problems = []
        for folder in self._result_folders():
            try:
                self._backend.open_folder(folder)
            except (OSError, ValueError):
                path = printable(str(folder))
                problems.append(self.catalog.text("gui.result.cannot_open", path=path))
        if problems:  # every one of them: a later message would hide an earlier one
            self._view.show_message("\n".join(problems))

    # --- Settings and welcome --------------------------------------------------------------------

    def save_settings(self, settings: Settings) -> None:
        """Save and apply at once (language, theme); told if the file cannot be written."""
        self._apply(settings)
        self._save(settings)
        self._show_inputs()
        self._show_output()
        if self._plan is not None and self.state is AppState.WAITING_DECISION:
            self._view.show_plan(self._plan_view(self._plan))
        if self._report is not None:  # the results, in the new language
            self._view.show_result(self._result_view(self._report, self.state))
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

    def _scanned(self, generation: int, found: int) -> None:
        """One event per folder: the latest count is shown at most every SCAN_MS (a large tree
        would otherwise queue seconds of redrawing on the UI thread)."""
        pending = self._scan_count is not None and self._scan_count[0] == generation
        self._scan_count = (generation, found)
        if not pending:
            self._view.after(SCAN_MS, lambda: self._show_scan_count(generation))

    def _show_scan_count(self, generation: int) -> None:
        if self._scan_count is None or self._scan_count[0] != generation:
            return  # an older analysis's timer: the count belongs to another one
        found = self._scan_count[1]
        self._scan_count = None
        if generation == self._generation and self.state is AppState.ANALYZING:
            self._view.show_scan(self.catalog.text("gui.scan.found", count=found))

    def _planned(self, plan: BatchPlan) -> None:
        self._plan = plan
        self._view.show_plan(self._plan_view(plan))
        self.page = 2
        self._set(AppState.WAITING_DECISION)

    def _started(self, index: int, total: int, name: str, left: float | None, icon: str) -> None:
        self._current = (index, total, name, left, icon)
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
        self.page = 4  # the results open by themselves (ADR-0029)
        self._set(state)
        opens = self.settings.open_output_when_done and not self._shutting_down
        if state is not AppState.CANCELLED and opens:
            self.open_results()

    def _unexpected(self, error: Exception) -> None:
        detail = printable(f"{type(error).__name__}: {error}")
        message = self.catalog.text("gui.app.unexpected_error", detail=detail)
        self._cancel = None
        self._set(AppState.READY)
        self._view.show_message(message)  # after the state: a view may clear it on a step change

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
        view = StateView(state, label, enabled, step_of(state), self.page, self._primary())
        self._view.show_state(view)

    def _show_inputs(self) -> None:
        rows = []
        for path in self._inputs:
            is_folder = path.is_dir()
            name = path.name or str(path)
            icon = icon_for(path, is_folder=is_folder)
            location = printable(str(path.parent))
            rows.append(InputRow(path, printable(name), location, is_folder, icon))
        self._view.show_inputs(tuple(rows))

    def _show_output(self) -> None:
        remembered = self.settings.last_output_folder
        suggestion = Path(remembered) if remembered else None
        if self._output_folder is None:
            label = self.catalog.text("gui.output.next_to_detail")
            choice = OutputChoice(OutputMode.NEXT_TO, None, suggestion, label)
        else:
            path = printable(str(self._output_folder))
            label = self.catalog.text("gui.output.folder", path=path)
            choice = OutputChoice(OutputMode.FOLDER, self._output_folder, suggestion, label)
        self._view.show_output_choice(choice)

    def _show_progress(self) -> None:
        if self._current is None:
            return
        index, total, name, left, icon = self._current
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
                icon=icon,
            )
        )

    def _plan_view(self, plan: BatchPlan) -> PlanView:
        rows: list[PlanRow] = []
        for item in plan.conversions:
            kind = RowKind.EXISTS if item.exists else RowKind.CONVERT
            icon = icon_of_format(item.detection.format)
            name, location = _shown(item.source)
            rows.append(PlanRow(kind, name, location, self._format(item), icon))
        for skipped in plan.skipped:
            reason = skip_reason(self.catalog, skipped)
            detail = f"{reason}. {skip_action(self.catalog, skipped)}"
            name, location = _shown(skipped.path, is_dir=skipped.is_dir)
            icon = icon_for(skipped.path, is_folder=skipped.is_dir)
            rows.append(PlanRow(RowKind.SKIPPED, name, location, detail, icon))
        for missing in plan.input_errors:
            detail = self.catalog.text("gui.plan.not_found")
            name, location = _shown(missing.path)
            icon = icon_for(missing.path, is_folder=False)  # it is not there: only its name
            rows.append(PlanRow(RowKind.MISSING, name, location, detail, icon))
        existing = len(plan.existing)
        summary = self.catalog.text(
            "gui.plan.summary",
            convert=len(plan.conversions),
            skipped=len(plan.skipped) + len(plan.input_errors),
            existing=existing,
        )
        asks = existing > 0 and self.settings.on_existing_output == "ask"
        stats = (
            self._stat("gui.plan.stat_convert", len(plan.conversions), Tone.ACCENT),
            self._stat("gui.plan.stat_skipped", len(plan.skipped) + len(plan.input_errors)),
            self._stat("gui.plan.stat_existing", existing, Tone.NEUTRAL),
        )
        return PlanView(summary, tuple(rows), asks, stats)

    def _stat(self, key: str, value: int, tone: Tone = Tone.WARNING) -> Stat:
        """A figure; a warning or a problem only when it is not zero."""
        return Stat(
            self.catalog.text(key), value, tone if value or tone is Tone.ACCENT else Tone.NEUTRAL
        )

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
            rows.append(ResultRow(*_shown(source), detail, icon))
        for skipped in report.skipped:
            reason = skip_reason(self.catalog, skipped)
            detail = f"{reason}. {skip_action(self.catalog, skipped)}"
            icon = icon_for(skipped.path, is_folder=skipped.is_dir)
            rows.append(ResultRow(*_shown(skipped.path), detail, icon))
        for root in report.unwritten_summaries:
            detail = self.catalog.text("gui.result.no_summary")
            rows.append(ResultRow(*_shown(root), detail, FOLDER))
        counts = self.catalog.text(
            "cli.summary",
            converted=count[OutcomeStatus.CONVERTED],
            skipped=len(report.skipped) + count[OutcomeStatus.KEPT],
            failed=count[OutcomeStatus.FAILED],
        )
        if count[OutcomeStatus.STOPPED]:
            counts += self.catalog.text("cli.summary_stopped", stopped=count[OutcomeStatus.STOPPED])
        headline = self.catalog.text(f"gui.state.{state.value}")
        stats = [
            self._stat("gui.result.stat_converted", count[OutcomeStatus.CONVERTED], Tone.ACCENT),
            self._stat("gui.result.stat_skipped", len(report.skipped) + count[OutcomeStatus.KEPT]),
            self._stat("gui.result.stat_failed", count[OutcomeStatus.FAILED], Tone.DANGER),
        ]
        if count[OutcomeStatus.STOPPED]:
            stats.append(self._stat("gui.result.stat_stopped", count[OutcomeStatus.STOPPED]))
        folders = self._result_folders(report)
        return ResultView(headline, counts, tuple(rows), folders, tuple(stats))

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


def _shown(path: Path, *, is_dir: bool = False) -> tuple[str, str]:
    """A path's name and folder as a view may show them: invisible and line-breaking
    characters escaped, as the CLI does (security review of 005)."""
    name = path.name + ("/" if is_dir else "")
    return printable(name), printable(str(path.parent))


def _key(path: Path) -> str:
    """How two inputs are the same: the same absolute, normalized path."""
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))
