"""Immutable data of a batch: the plan the user reviews and the report of what happened."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path

from clearmd.backend.schemas.errors import ErrorCode, SkipReason
from clearmd.backend.schemas.formats import FormatId, Strategy
from clearmd.backend.schemas.notes import ConversionNote


class DetectionMethod(StrEnum):
    EXTENSION = "extension"
    CONTENT = "content"


@dataclass(frozen=True)
class Detection:
    format: FormatId
    method: DetectionMethod

    @property
    def by_content(self) -> bool:
        return self.method is DetectionMethod.CONTENT


@dataclass(frozen=True)
class PlannedConversion:
    """One file to convert. ``target`` lives in ``output_root / "OutputMD"``."""

    source: Path
    output_root: Path
    target: Path
    detection: Detection
    exists: bool
    cost: float
    strategy: Strategy = Strategy.FULL


@dataclass(frozen=True)
class SkippedItem:
    path: Path
    reason: SkipReason
    is_dir: bool = False
    # When a limit is the reason (UX contract §3): the file's value and the limit, in the unit of
    # the reason (bytes for sizes and memory, a count for entries and levels, a ratio).
    measured: float | None = None
    limit: float | None = None
    # The input it was found under, and the output root whose summary lists it (set by planning).
    input: Path | None = None
    input_is_dir: bool = False
    output_root: Path | None = None


class InputProblem(StrEnum):
    NOT_FOUND = "not_found"


@dataclass(frozen=True)
class InputError:
    path: Path
    problem: InputProblem


@dataclass(frozen=True)
class PlanWarning:
    """A planned file whose estimated time exceeds the time limit (AC-43): tried anyway, last."""

    item: PlannedConversion
    estimated_seconds: float
    limit_seconds: float


@dataclass(frozen=True)
class BatchPlan:
    """Everything computed before writing anything, already in execution order."""

    conversions: tuple[PlannedConversion, ...]
    skipped: tuple[SkippedItem, ...]
    input_errors: tuple[InputError, ...]
    warnings: tuple[PlanWarning, ...] = ()

    @property
    def is_empty(self) -> bool:
        return not self.conversions

    @property
    def existing(self) -> tuple[PlannedConversion, ...]:
        return tuple(item for item in self.conversions if item.exists)

    @property
    def output_roots(self) -> tuple[Path, ...]:
        return tuple(dict.fromkeys(item.output_root for item in self.conversions))


class OutcomeStatus(StrEnum):
    CONVERTED = "converted"
    FAILED = "failed"
    # Stopped by the time or memory limit: the file is not damaged, just too big (AC-44).
    STOPPED = "stopped"
    KEPT = "kept"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class ConversionResult:
    """What a converter returns: the Markdown, and what it could not do faithfully (ADR-0022)."""

    markdown: str
    notes: tuple[ConversionNote, ...] = ()


@dataclass(frozen=True)
class ConversionOutcome:
    item: PlannedConversion
    status: OutcomeStatus
    error: ErrorCode | None = None
    detail: str = ""
    seconds: float = 0.0
    notes: tuple[ConversionNote, ...] = ()
    limit: float | None = None  # for a stop: the limit it reached (seconds or bytes)

    @property
    def share_done(self) -> int:
        """How far a stopped file probably got, by the estimate: 1-99 %, never 100 (AC-44)."""
        if self.item.cost <= 0:
            return 99
        return max(1, min(99, round(100 * self.seconds / self.item.cost)))


@dataclass(frozen=True)
class OutputRootReport:
    """What one ClearMD_Output folder's summary describes."""

    root: Path
    started_at: datetime
    finished_at: datetime
    outcomes: tuple[ConversionOutcome, ...]
    skipped: tuple[SkippedItem, ...]
    cancelled: bool


@dataclass(frozen=True)
class BatchReport:
    """What happened, as data and codes; the summary writer turns it into words (ADR-0012)."""

    started_at: datetime
    finished_at: datetime
    outcomes: tuple[ConversionOutcome, ...]
    skipped: tuple[SkippedItem, ...]
    input_errors: tuple[InputError, ...]
    cancelled: bool
    # Output roots whose Resumen_ClearMD.md could not be written (disk full, ...).
    unwritten_summaries: tuple[Path, ...] = ()
