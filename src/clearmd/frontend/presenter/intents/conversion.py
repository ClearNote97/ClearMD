"""The conversion: the confirmed plan runs off the UI thread; each file's timer, the batch's end."""

from collections.abc import Callable
from functools import partial

from clearmd.backend.api import CancelToken, changed_since_result
from clearmd.backend.schemas.events import (
    BatchEvent,
    ConversionFinished,
    ConversionProgress,
    ConversionStarted,
)
from clearmd.backend.schemas.models import BatchReport, OutcomeStatus, PlannedConversion
from clearmd.frontend.presenter.background import Background
from clearmd.frontend.presenter.display import Display
from clearmd.frontend.presenter.icons import icon_of_format
from clearmd.frontend.presenter.intents.reset import unexpected
from clearmd.frontend.presenter.ports import Backend
from clearmd.frontend.presenter.screens.results import result_view
from clearmd.frontend.presenter.session import Session
from clearmd.frontend.presenter.state import AppState, Tool
from clearmd.i18n import printable

TICK_MILLISECONDS = 1000


def existing_decision(
    setting: str, answer: bool | str | None
) -> Callable[[PlannedConversion], bool]:
    """Whether to replace an existing result: the setting, or the user's answer when it asks."""
    choice = setting if setting != "ask" else answer
    if choice == "changed":
        return changed_since_result
    replace = choice is True or choice == "overwrite"
    return lambda item: replace


class Conversion:
    def __init__(
        self,
        session: Session,
        display: Display,
        backend: Backend,
        background: Background,
        clock: Callable[[], float],
        open_results: Callable[[], None],
    ) -> None:
        self._session = session
        self._display = display
        self._backend = backend
        self._background = background
        self._clock = clock
        self._open_results = open_results

    def confirm(self, overwrite: bool | str | None = None) -> None:
        """Convert the plan. ``overwrite`` answers the question about existing outputs: True,
        False, or "changed" (only those whose original changed, feature 028)."""
        s = self._session
        if s.state is not AppState.WAITING_DECISION or not s.plan:
            return
        plan = s.plan
        if not plan.conversions:
            return
        decide = existing_decision(s.settings.on_existing_output, overwrite)
        generation = self._background.next_generation()
        s.cancel = token = CancelToken()
        language = s.catalog.language  # read here: the worker never touches the presenter
        summary_pdf = s.settings.summary_format in {"markdown_pdf", "pdf"}
        summary_markdown = s.settings.summary_format != "pdf"  # "pdf": the PDF alone (020)
        images = s.settings.images == "folder" and s.tool is Tool.CONVERT  # Split, Merge: none
        s.done = s.kept = 0
        s.stopped = None
        s.current = None
        s.page = 3  # the progress is shown on Convert (ADR-0029)
        self._display.set_state(AppState.CONVERTING)

        def on_event(event: BatchEvent) -> None:
            if isinstance(event, ConversionStarted):
                left, name = event.seconds_left, event.item.source.name
                icon = icon_of_format(event.item.detection.format)
                name = printable(name)
                self._background.later(
                    generation, lambda: self._started(event.total, name, left, icon)
                )
            elif isinstance(event, ConversionProgress):
                pages = (event.done, event.pages)
                self._background.later(generation, lambda: setattr(s, "pages", pages))
            elif isinstance(event, ConversionFinished):
                kept = event.outcome.status is OutcomeStatus.KEPT
                self._background.later(generation, lambda: self._finished_one(kept=kept))

        def work() -> None:
            try:
                report = self._backend.run_batch(
                    plan,
                    overwrite=decide,
                    on_event=on_event,
                    cancel=token,
                    language=language,
                    summary_pdf=summary_pdf,
                    summary_markdown=summary_markdown,
                    images=images,
                )
            except Exception as error:  # noqa: BLE001 -- told to the user, the app goes on
                self._background.later(generation, partial(unexpected, s, self._display, error))
                return
            self._background.later(generation, lambda: self._converted(report))

        # this file's timer
        self._display.view.after(TICK_MILLISECONDS, lambda: self._tick(generation))
        self._background.spawn(work)

    def cancel(self) -> None:
        """A batch stops its current file at once (ADR-0015)."""
        s = self._session
        if s.cancel is not None:
            s.cancel.cancel()
            self._display.view.show_message(s.catalog.text("gui.progress.cancelling"))

    def _started(self, total: int, name: str, left: float | None, icon: str) -> None:
        """ "File 1 of 5" counts what is written: a kept result is no file of the task (F3-04)."""
        s = self._session
        s.current = (s.done + 1, total - s.kept, name, left, icon)
        s.pages = None
        s.started_at = self._clock()
        self._display.show_progress()

    def _finished_one(self, *, kept: bool = False) -> None:
        s = self._session
        if kept:
            s.kept += 1
        else:
            s.done += 1

    def _tick(self, generation: int) -> None:
        s = self._session
        if generation != s.generation or s.state is not AppState.CONVERTING:
            return
        self._display.show_progress()
        self._display.view.after(TICK_MILLISECONDS, lambda: self._tick(generation))

    def _converted(self, report: BatchReport) -> None:
        s = self._session
        s.report = report
        s.cancel = None
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
        self._display.view.show_result(result_view(s.catalog, report, state))
        s.page = 4  # the results open by themselves (ADR-0029)
        self._display.set_state(state)
        opens = s.settings.open_output_when_done and not s.shutting_down
        # Only when all went well: a folder opening over the list would hide what failed (F1-06).
        if state is AppState.FINISHED and opens:
            self._open_results()
