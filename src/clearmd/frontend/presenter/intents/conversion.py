"""The conversion: the confirmed plan runs off the UI thread; each file's timer, the batch's end."""

from collections.abc import Callable
from functools import partial

from clearmd.backend.api import CancelToken
from clearmd.backend.schemas.events import BatchEvent, ConversionFinished, ConversionStarted
from clearmd.backend.schemas.models import BatchReport, OutcomeStatus
from clearmd.frontend.presenter.background import Background
from clearmd.frontend.presenter.display import Display
from clearmd.frontend.presenter.icons import icon_of_format
from clearmd.frontend.presenter.intents.reset import unexpected
from clearmd.frontend.presenter.ports import Backend
from clearmd.frontend.presenter.screens.results import result_view
from clearmd.frontend.presenter.session import Session
from clearmd.frontend.presenter.state import AppState
from clearmd.i18n import printable

TICK_MILLISECONDS = 1000


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

    def confirm(self, overwrite: bool | None = None) -> None:
        """Convert the plan. ``overwrite`` answers the question about existing outputs."""
        s = self._session
        if s.state is not AppState.WAITING_DECISION or not s.plan:
            return
        plan = s.plan
        if not plan.conversions:
            return
        choice = s.settings.on_existing_output
        overwrites = choice == "overwrite" if choice != "ask" else bool(overwrite)
        generation = self._background.next_generation()
        s.cancel = token = CancelToken()
        language = s.catalog.language  # read here: the worker never touches the presenter
        summary_pdf = s.settings.summary_format == "markdown_pdf"
        images = s.settings.images == "folder"
        s.done = 0
        s.current = None
        s.page = 3  # the progress is shown on Convert (ADR-0029)
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

    def _started(self, index: int, total: int, name: str, left: float | None, icon: str) -> None:
        s = self._session
        s.current = (index, total, name, left, icon)
        s.started_at = self._clock()
        self._display.show_progress()

    def _finished_one(self) -> None:
        self._session.done += 1

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
        if state is not AppState.CANCELLED and opens:
            self._open_results()
