"""What the presenter needs from a view (one per toolkit) and from the backend (the facade)."""

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Protocol

from clearmd.backend.api import load_settings, open_folder, plan_batch, run_batch, save_settings
from clearmd.backend.schemas.models import BatchPlan, BatchReport
from clearmd.backend.schemas.settings import Settings, SettingsWarning
from clearmd.frontend.presenter.models import (
    InputRow,
    OutputChoice,
    PlanView,
    ProgressView,
    ResultView,
    StateView,
)
from clearmd.i18n import Catalog


class View(Protocol):
    """A passive view: it draws what it is given and calls the presenter's intents."""

    def after(self, milliseconds: int, callback: Callable[[], None]) -> None:
        """Run ``callback`` on the UI thread, after ``milliseconds`` (0: as soon as possible).
        Safe to call from any thread."""

    def show_state(self, state: StateView) -> None: ...
    def show_inputs(self, rows: tuple[InputRow, ...]) -> None: ...
    def show_output_choice(self, choice: OutputChoice) -> None: ...
    def show_scan(self, text: str) -> None: ...
    def show_plan(self, plan: PlanView) -> None: ...
    def show_progress(self, progress: ProgressView) -> None: ...
    def show_result(self, result: ResultView) -> None: ...
    def show_message(self, text: str) -> None: ...
    def show_welcome(self, steps: tuple[str, ...]) -> None: ...
    def apply_theme(self, theme: str) -> None: ...
    def apply_language(self, catalog: Catalog) -> None: ...


class Backend(Protocol):
    def load_settings(self) -> tuple[Settings, tuple[SettingsWarning, ...]]: ...
    def save_settings(self, settings: Settings) -> None: ...
    def open_folder(self, path: Path) -> None: ...
    def plan_batch(self, inputs: Sequence[Path], **options: Any) -> BatchPlan: ...
    def run_batch(self, plan: BatchPlan, **options: Any) -> BatchReport: ...


class ApiBackend:
    """The real backend: ClearMD's facade (ADR-0014)."""

    def load_settings(self) -> tuple[Settings, tuple[SettingsWarning, ...]]:
        return load_settings()

    def save_settings(self, settings: Settings) -> None:
        save_settings(settings)

    def open_folder(self, path: Path) -> None:
        open_folder(path)

    def plan_batch(self, inputs: Sequence[Path], **options: Any) -> BatchPlan:
        return plan_batch(inputs, **options)

    def run_batch(self, plan: BatchPlan, **options: Any) -> BatchReport:
        return run_batch(plan, **options)
