"""The analysis: the plan is computed off the UI thread; nothing is written until the user
confirms. The scan's count, its cancel and the plan's arrival."""

from functools import partial

from clearmd.backend.api import CancelToken, Cut, Keep, SplitSpec, Strategy
from clearmd.backend.schemas.events import BatchEvent, ScanProgress
from clearmd.backend.schemas.models import BatchPlan
from clearmd.frontend.presenter.background import Background
from clearmd.frontend.presenter.display import Display
from clearmd.frontend.presenter.intents.reset import unexpected
from clearmd.frontend.presenter.ports import Backend
from clearmd.frontend.presenter.screens.review import plan_view
from clearmd.frontend.presenter.session import Session
from clearmd.frontend.presenter.state import AppState, Tool

SCAN_MS = 100  # the scan count is shown at most this often (code review of 005)


def split_spec(s: Session) -> SplitSpec | None:
    """Split's cut and what to keep, from the settings; ``None`` for Convert (feature 023)."""
    if s.tool is not Tool.SPLIT:
        return None
    settings = s.settings
    cut = Cut(settings.split_cut)
    size = settings.split_parts if cut is Cut.PARTS else settings.split_pages
    return SplitSpec(cut, size, Keep(settings.split_keep))


class Analysis:
    def __init__(
        self, session: Session, display: Display, backend: Backend, background: Background
    ) -> None:
        self._session = session
        self._display = display
        self._backend = backend
        self._background = background

    def analyze(self) -> None:
        """Compute the plan (off the UI thread); nothing is written until the user confirms."""
        s = self._session
        if s.state is not AppState.READY or not s.inputs:
            return
        generation = self._background.next_generation()
        inputs = list(s.inputs)
        s.page = 1  # the scan is told on Choose; Review opens with the plan
        options = {
            "recursive": s.settings.recursive,
            "output_root": s.output_folder,
            "html_strategy": Strategy(s.settings.html_strategy),
            "split": split_spec(s),
        }
        s.cancel = token = CancelToken()
        s.scan_count = None
        self._display.set_state(AppState.ANALYZING)
        self._display.view.show_scan(s.catalog.text("gui.scan.started"))

        def on_event(event: BatchEvent) -> None:
            if isinstance(event, ScanProgress):
                self._background.later(generation, lambda: self.scanned(generation, event.found))

        def work() -> None:
            try:
                plan = self._backend.plan_batch(inputs, on_event=on_event, cancel=token, **options)
            except Exception as error:  # noqa: BLE001 -- told to the user, the app goes on
                self._background.later(generation, partial(unexpected, s, self._display, error))
                return
            self._background.later(generation, lambda: self._planned(plan))

        self._background.spawn(work)

    def cancel(self) -> None:
        """An analysis is dropped: whatever it returns later is ignored."""
        s = self._session
        self._background.next_generation()  # whatever it returns is dropped
        if s.cancel is not None:
            s.cancel.cancel()  # and the scan stops at its next folder
        s.cancel = None
        s.page = 1
        self._display.set_state(AppState.READY)

    def scanned(self, generation: int, found: int) -> None:
        """One event per folder: the latest count is shown at most every SCAN_MS (a large tree
        would otherwise queue seconds of redrawing on the UI thread)."""
        s = self._session
        pending = s.scan_count is not None and s.scan_count[0] == generation
        s.scan_count = (generation, found)
        if not pending:
            self._display.view.after(SCAN_MS, lambda: self._show_scan_count(generation))

    def _show_scan_count(self, generation: int) -> None:
        s = self._session
        if s.scan_count is None or s.scan_count[0] != generation:
            return  # an older analysis's timer: the count belongs to another one
        found = s.scan_count[1]
        s.scan_count = None
        if generation == s.generation and s.state is AppState.ANALYZING:
            self._display.view.show_scan(s.catalog.text("gui.scan.found", count=found))

    def _planned(self, plan: BatchPlan) -> None:
        s = self._session
        s.plan = plan
        s.plan_id += 1
        self._display.view.show_plan(
            plan_view(s.catalog, plan, s.settings.on_existing_output, s.plan_id)
        )
        s.page = 2
        self._display.set_state(AppState.WAITING_DECISION)
