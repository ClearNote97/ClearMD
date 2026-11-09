"""Progress events that any interface can render (ADR-0013). They run in the caller's thread."""

from dataclasses import dataclass
from pathlib import Path

from clearmd.backend.schemas.models import (
    BatchPlan,
    BatchReport,
    ConversionOutcome,
    PlannedConversion,
)


@dataclass(frozen=True)
class ScanProgress:
    found: int
    current: Path


@dataclass(frozen=True)
class PlanReady:
    plan: BatchPlan


@dataclass(frozen=True)
class ConversionStarted:
    index: int
    total: int
    item: PlannedConversion
    # Estimated seconds left for the whole batch; None until one file was measured (AC-40).
    seconds_left: float | None = None


@dataclass(frozen=True)
class ConversionProgress:
    """How far the current file has got: "page 40 of 120" (audit 2026-11-08, 3B)."""

    index: int
    total: int
    item: PlannedConversion
    done: int
    pages: int


@dataclass(frozen=True)
class ConversionFinished:
    index: int
    total: int
    outcome: ConversionOutcome


@dataclass(frozen=True)
class BatchFinished:
    report: BatchReport


type BatchEvent = (
    ScanProgress
    | PlanReady
    | ConversionStarted
    | ConversionProgress
    | ConversionFinished
    | BatchFinished
)
