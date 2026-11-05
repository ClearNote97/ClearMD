"""The presenter: the state, the intents and every text, once for every GUI (ADR-0026).

The view is passive (``ports.View``). Planning and converting run off the UI thread (``spawn``);
their events come back through ``view.after(0, …)``, so the presenter only changes on the UI
thread. Each piece of work carries a generation: what a cancelled analysis returns later is
dropped.
"""

import os
import time
from collections.abc import Callable, Sequence
from dataclasses import replace
from functools import partial
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from clearmd.backend.api import (
    CancelToken,
    Strategy,
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
)
from clearmd.backend.schemas.settings import CHOICES, Settings, valid_path_setting
from clearmd.frontend.presenter.background import Background
from clearmd.frontend.presenter.display import Display
from clearmd.frontend.presenter.icons import icon_of_format
from clearmd.frontend.presenter.ports import ApiBackend, Backend, View
from clearmd.frontend.presenter.screens.choose import key
from clearmd.frontend.presenter.screens.results import result_folders, result_view
from clearmd.frontend.presenter.screens.review import plan_view
from clearmd.frontend.presenter.session import Session
from clearmd.frontend.presenter.state import WORKING, AppState
from clearmd.frontend.presenter.system_theme import detect_system_theme
from clearmd.i18n import Catalog, load_catalog, printable, resolve_language

SCAN_MS = 100  # the scan count is shown at most this often (code review of 005)
TICK_MILLISECONDS = 1000


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
        self._session = Session()
        self._display = Display(view, self._session, clock)
        self._background = Background(view, self._session, spawn)

    @property
    def state(self) -> AppState:
        return self._session.state

    @property
    def page(self) -> int:
        return self._session.page

    @property
    def settings(self) -> Settings:
        return self._session.settings

    @property
    def catalog(self) -> Catalog:
        return self._session.catalog

    # --- Start -----------------------------------------------------------------------------------

    def start(self) -> None:
        """Read the settings, apply the language and the theme, show the welcome if wanted."""
        settings, warnings = self._backend.load_settings()
        self._apply(settings)
        self._display.show_inputs()
        self._display.show_output()
        self._display.set_state(AppState.READY)
        if warnings:  # after the first state: a view may clear its message on a step change
            lines = (
                self._session.catalog.text(f"settings.{warning.problem.value}", setting=warning.key)
                for warning in warnings
            )
            self._view.show_message("\n".join(printable(line) for line in lines))
        if self._session.settings.show_welcome:
            self._view.show_welcome(
                tuple(self._session.catalog.text(f"gui.welcome.step{n}") for n in (1, 2, 3))
            )

    def _apply(self, settings: Settings) -> None:
        self._session.settings = settings
        self._session.catalog = load_catalog(resolve_language(None, settings.language))
        self._view.apply_language(self._session.catalog)
        theme = settings.theme if settings.theme != "system" else self._detect_theme()
        theme = theme if theme in {"light", "dark"} else "light"
        if theme != self._session.theme:  # redrawing the lists for nothing loses their selection
            self._session.theme = theme
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
        return self._session.output_folder

    # --- Inputs and the output -------------------------------------------------------------------

    def add_paths(self, paths: Sequence[Path]) -> None:
        """Files or folders, from the dialogs or dropped on the window; never listed twice."""
        known = {key(path) for path in self._session.inputs}
        new: list[Path] = []
        for path in paths:
            absolute = Path(os.path.abspath(path))
            if key(absolute) not in known:
                known.add(key(absolute))
                new.append(absolute)
        if not new or not self._editable():  # nothing new: the plan stays (C7-4)
            return
        self._session.inputs.extend(new)
        self._display.show_inputs()
        self._display.set_state(self._session.state)

    def remove_input(self, path: Path) -> None:
        self.remove_inputs([path])

    def remove_inputs(self, paths: Sequence[Path]) -> None:
        """Remove several at once: one redraw, whatever their number (code review of 007)."""
        gone = {key(Path(path)) for path in paths}
        kept = [known for known in self._session.inputs if key(known) not in gone]
        if len(kept) == len(self._session.inputs) or not self._editable():
            return
        self._session.inputs = kept
        self._display.show_inputs()
        self._display.set_state(self._session.state)

    def clear_inputs(self) -> None:
        if not self._session.inputs or not self._editable():
            return
        self._session.inputs.clear()
        self._display.show_inputs()
        self._display.set_state(self._session.state)

    def choose_output_next_to(self) -> None:
        if self._session.output_folder is None or not self._editable():
            return
        self._session.output_folder = None
        self._display.show_output()
        self._display.set_state(self._session.state)

    def choose_output_folder(self, folder: Path) -> None:
        """Results in ``folder``, remembered as the suggestion for next time (ADR-0016) when its
        path can be stored (a name with control characters still receives the results)."""
        chosen = Path(os.path.abspath(folder))
        if chosen == self._session.output_folder or not self._editable():
            return
        self._session.output_folder = chosen
        self._display.show_output()
        self._display.set_state(self._session.state)
        if valid_path_setting(str(self._session.output_folder)):
            self._save(
                replace(self._session.settings, last_output_folder=str(self._session.output_folder))
            )

    def _editable(self) -> bool:
        """Inputs and output change outside the work only; a change drops a plan or a result
        (it was made from the inputs as they were, ADR-0029)."""
        if self._session.state in WORKING:
            return False
        if self._session.state is not AppState.READY:
            self._session.plan = None
            self._session.report = None
            self._session.state = AppState.READY
            self._view.forget_work()
        return True

    # --- Pages (ADR-0029) ------------------------------------------------------------------------

    def go_to(self, page: int) -> None:
        """Show a step; only what is on screen changes."""
        if 1 <= page <= 4:
            self._session.page = page
            self._display.set_state(self._session.state)

    def press_primary(self, overwrite: bool | None = None) -> None:
        """The page's primary action: Next, Next, Convert, Open results folder."""
        if not self._display.primary().enabled:
            return
        if self._session.page == 1:
            if self._session.state is AppState.WAITING_DECISION:
                self.go_to(2)
            else:
                self._editable()  # after a batch: a new plan (security audit of 007, N-1)
                self.analyze()
        elif self._session.page == 2:
            self.go_to(3)
        elif self._session.page == 3:
            self.confirm(overwrite)
        else:
            self.open_results()

    def convert_more(self, *, keep: bool) -> None:
        """From the results to Choose again, with the chosen files or without them."""
        if self._session.state in WORKING:
            return
        self._session.plan = None
        self._session.report = None
        self._view.forget_work()  # nothing of the last batch stays on screen (007, A7-1)
        if not keep:
            self._session.inputs.clear()
        self._session.page = 1
        self._display.show_inputs()
        self._display.set_state(AppState.READY)

    # --- Plan, confirm, convert ------------------------------------------------------------------

    def analyze(self) -> None:
        """Compute the plan (off the UI thread); nothing is written until the user confirms."""
        if self._session.state is not AppState.READY or not self._session.inputs:
            return
        generation = self._background.next_generation()
        inputs = list(self._session.inputs)
        self._session.page = 1  # the scan is told on Choose; Review opens with the plan
        options = {
            "recursive": self._session.settings.recursive,
            "output_root": self._session.output_folder,
            "html_strategy": Strategy(self._session.settings.html_strategy),
        }
        self._session.cancel = token = CancelToken()
        self._session.scan_count = None
        self._display.set_state(AppState.ANALYZING)
        self._view.show_scan(self._session.catalog.text("gui.scan.started"))

        def on_event(event: BatchEvent) -> None:
            if isinstance(event, ScanProgress):
                self._background.later(generation, lambda: self._scanned(generation, event.found))

        def work() -> None:
            try:
                plan = self._backend.plan_batch(inputs, on_event=on_event, cancel=token, **options)
            except Exception as error:  # noqa: BLE001 -- told to the user, the app goes on
                self._background.later(generation, partial(self._unexpected, error))
                return
            self._background.later(generation, lambda: self._planned(plan))

        self._background.spawn(work)

    def confirm(self, overwrite: bool | None = None) -> None:
        """Convert the plan. ``overwrite`` answers the question about existing outputs."""
        if self._session.state is not AppState.WAITING_DECISION or not self._session.plan:
            return
        plan = self._session.plan
        if not plan.conversions:
            return
        choice = self._session.settings.on_existing_output
        overwrites = choice == "overwrite" if choice != "ask" else bool(overwrite)
        generation = self._background.next_generation()
        self._session.cancel = token = CancelToken()
        language = (
            self._session.catalog.language
        )  # read here: the worker never touches the presenter
        summary_pdf = self._session.settings.summary_format == "markdown_pdf"
        images = self._session.settings.images == "folder"
        self._session.done = 0
        self._session.current = None
        self._session.page = 3  # the progress is shown on Convert (ADR-0029)
        self._display.set_state(AppState.CONVERTING)

        def on_event(event: BatchEvent) -> None:
            if isinstance(event, ConversionStarted):
                left, name = event.seconds_left, event.item.source.name
                icon = icon_of_format(event.item.detection.format)
                name = printable(name)
                self._background.later(
                    generation, lambda: self._started(event.index, event.total, name, left, icon)
                )
            elif isinstance(event, ConversionFinished):
                self._background.later(generation, self._finished_one)

        def work() -> None:
            try:
                report = self._backend.run_batch(
                    plan,
                    overwrite=lambda item: overwrites,
                    on_event=on_event,
                    cancel=token,
                    language=language,
                    summary_pdf=summary_pdf,
                    images=images,
                )
            except Exception as error:  # noqa: BLE001 -- told to the user, the app goes on
                self._background.later(generation, partial(self._unexpected, error))
                return
            self._background.later(generation, lambda: self._converted(report))

        self._view.after(TICK_MILLISECONDS, lambda: self._tick(generation))  # this file's timer
        self._background.spawn(work)

    def cancel(self) -> None:
        """Stop now: an analysis is dropped; a batch stops its current file at once (ADR-0015)."""
        if self._session.state is AppState.ANALYZING:
            self._background.next_generation()  # whatever it returns is dropped
            if self._session.cancel is not None:
                self._session.cancel.cancel()  # and the scan stops at its next folder
            self._session.cancel = None
            self._session.page = 1
            self._display.set_state(AppState.READY)
        elif self._session.state is AppState.CONVERTING and self._session.cancel is not None:
            self._session.cancel.cancel()
            self._view.show_message(self._session.catalog.text("gui.progress.cancelling"))

    def shutdown(self) -> None:
        """The window is closing: a batch may still end (its summary is written), but nothing
        opens afterwards (adversarial review of 005)."""
        self._session.shutting_down = True

    def back(self) -> None:
        """From the plan or the result, to the inputs again (they are kept)."""
        self.convert_more(keep=True)

    def open_results(self) -> None:
        problems = []
        for folder in result_folders(self._session.report):
            try:
                self._backend.open_folder(folder)
            except (OSError, ValueError):
                path = printable(str(folder))
                problems.append(self._session.catalog.text("gui.result.cannot_open", path=path))
        if problems:  # every one of them: a later message would hide an earlier one
            self._view.show_message("\n".join(problems))

    # --- Settings and welcome --------------------------------------------------------------------

    def save_settings(self, settings: Settings) -> None:
        """Save and apply at once (language, theme); told if the file cannot be written."""
        old = self._session.settings
        if (old.recursive, old.html_strategy) != (settings.recursive, settings.html_strategy):
            self._editable()  # these change what a plan holds: it is made again (007, I-1)
        self._apply(settings)
        self._save(settings)
        self._display.show_inputs()
        self._display.show_output()
        if self._session.plan is not None and self._session.state is AppState.WAITING_DECISION:
            self._view.show_plan(
                plan_view(
                    self._session.catalog,
                    self._session.plan,
                    self._session.settings.on_existing_output,
                    self._session.plan_id,
                )
            )
        if self._session.report is not None:  # the results, in the new language
            self._view.show_result(
                result_view(self._session.catalog, self._session.report, self._session.state)
            )
        self._display.set_state(self._session.state)

    def choose_summary_format(self, summary_format: str) -> None:
        """Markdown, or Markdown + PDF: chosen on step 1 and remembered (ADR-0031)."""
        valid = summary_format in CHOICES["summary_format"]
        if (
            not valid
            or summary_format == self._session.settings.summary_format
            or self._session.state in WORKING
        ):
            self._display.show_output()  # the radio buttons show the choice as it is
            return
        self.save_settings(replace(self._session.settings, summary_format=summary_format))

    def choose_images(self, images: str) -> None:
        """Images left out, or in a folder next to each Markdown: chosen on step 1 (ADR-0033)."""
        valid = images in CHOICES["images"]
        if not valid or images == self._session.settings.images or self._session.state in WORKING:
            self._display.show_output()
            return
        self.save_settings(replace(self._session.settings, images=images))

    def restore_defaults(self) -> None:
        self.save_settings(Settings())

    def dismiss_welcome(self, *, show_again: bool) -> None:
        if not show_again:
            self._save(replace(self._session.settings, show_welcome=False))

    def _save(self, settings: Settings) -> None:
        self._session.settings = settings
        try:
            self._backend.save_settings(settings)
        except (OSError, ValueError):
            self._view.show_message(self._session.catalog.text("gui.settings.not_saved"))

    # --- Work coming back (UI thread) ------------------------------------------------------------

    def _scanned(self, generation: int, found: int) -> None:
        """One event per folder: the latest count is shown at most every SCAN_MS (a large tree
        would otherwise queue seconds of redrawing on the UI thread)."""
        pending = self._session.scan_count is not None and self._session.scan_count[0] == generation
        self._session.scan_count = (generation, found)
        if not pending:
            self._view.after(SCAN_MS, lambda: self._show_scan_count(generation))

    def _show_scan_count(self, generation: int) -> None:
        if self._session.scan_count is None or self._session.scan_count[0] != generation:
            return  # an older analysis's timer: the count belongs to another one
        found = self._session.scan_count[1]
        self._session.scan_count = None
        if generation == self._session.generation and self._session.state is AppState.ANALYZING:
            self._view.show_scan(self._session.catalog.text("gui.scan.found", count=found))

    def _planned(self, plan: BatchPlan) -> None:
        self._session.plan = plan
        self._session.plan_id += 1
        self._view.show_plan(
            plan_view(
                self._session.catalog,
                plan,
                self._session.settings.on_existing_output,
                self._session.plan_id,
            )
        )
        self._session.page = 2
        self._display.set_state(AppState.WAITING_DECISION)

    def _started(self, index: int, total: int, name: str, left: float | None, icon: str) -> None:
        self._session.current = (index, total, name, left, icon)
        self._session.started_at = self._clock()
        self._display.show_progress()

    def _finished_one(self) -> None:
        self._session.done += 1

    def _tick(self, generation: int) -> None:
        if generation != self._session.generation or self._session.state is not AppState.CONVERTING:
            return
        self._display.show_progress()
        self._view.after(TICK_MILLISECONDS, lambda: self._tick(generation))

    def _converted(self, report: BatchReport) -> None:
        self._session.report = report
        self._session.cancel = None
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
        self._view.show_result(result_view(self._session.catalog, report, state))
        self._session.page = 4  # the results open by themselves (ADR-0029)
        self._display.set_state(state)
        opens = self._session.settings.open_output_when_done and not self._session.shutting_down
        if state is not AppState.CANCELLED and opens:
            self.open_results()

    def _unexpected(self, error: Exception) -> None:
        detail = printable(f"{type(error).__name__}: {error}")
        message = self._session.catalog.text("gui.app.unexpected_error", detail=detail)
        self._session.cancel = None
        self._session.plan = None
        self._session.report = None
        self._view.forget_work()
        self._display.set_state(AppState.READY)
        self._view.show_message(message)  # after the state: a view may clear it on a step change

    # --- What the view draws ---------------------------------------------------------------------
