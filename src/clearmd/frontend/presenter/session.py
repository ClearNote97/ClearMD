"""The presenter's mutable work: what the user chose, the plan, the report, the step on screen."""

from pathlib import Path

from clearmd.backend.api import CancelToken
from clearmd.backend.schemas.models import BatchPlan, BatchReport
from clearmd.backend.schemas.settings import Settings
from clearmd.frontend.presenter.state import HOME, AppState, Tool
from clearmd.i18n import Catalog, load_catalog


class Session:
    def __init__(self) -> None:
        self.settings = Settings()
        self.catalog: Catalog = load_catalog("en")
        self.state = AppState.READY
        self.inputs: list[Path] = []
        self.output_folder: Path | None = None
        self.plan: BatchPlan | None = None
        self.report: BatchReport | None = None
        self.cancel: CancelToken | None = None
        self.generation = 0
        # index, total, name, seconds left, icon
        self.current: tuple[int, int, str, float | None, str] | None = None
        self.started_at = 0.0
        self.done = 0
        self.details: str | None = None  # what "Copy Details" copies after an error (D3)
        self.pages: tuple[int, int] | None = None  # the current file's page N of M (3B)
        self.theme: str | None = None
        self.shutting_down = False  # the window is closing: nothing is opened any more
        self.scan_count: tuple[int, int] | None = None  # (generation, latest count), SCAN_MS
        self.page = HOME  # the step on screen (ADR-0029); the start screen first (feature 023)
        self.tool = Tool.CONVERT
        self.plan_id = 0  # each plan's own number (security audit of 007, F-2)
