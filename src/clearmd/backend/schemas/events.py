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


@dataclass(frozen=True)
class ConversionFinished:
    index: int
    total: int
    outcome: ConversionOutcome


@dataclass(frozen=True)
class BatchFinished:
    report: BatchReport


type BatchEvent = ScanProgress | PlanReady | ConversionStarted | ConversionFinished | BatchFinished
