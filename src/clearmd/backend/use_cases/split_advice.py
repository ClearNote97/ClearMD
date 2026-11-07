"""Which PDFs of a Convert batch are too large, and into how many parts to split them (feature
025): each part should fit the time and memory limits with a margin (ADR-0015, ADR-0044)."""

import math
from collections.abc import Sequence
from pathlib import Path

from clearmd.backend.schemas.errors import ErrorCode, SkipReason
from clearmd.backend.schemas.formats import FormatId
from clearmd.backend.schemas.models import BatchPlan, BatchReport, OutcomeStatus

MARGIN = 0.6  # a part should take at most 60 % of a limit
FEWEST, MOST = 2, 1000


def recommended_parts(
    seconds: float = 0.0,
    time_limit: float = 1.0,
    memory: float = 0.0,
    memory_limit: float = 1.0,
) -> int:
    """Enough parts for each to take at most MARGIN of the time and of the memory limit."""
    by_time = math.ceil(seconds / (MARGIN * time_limit)) if time_limit > 0 else FEWEST
    by_memory = math.ceil(memory / (MARGIN * memory_limit)) if memory_limit > 0 else FEWEST
    return max(FEWEST, min(MOST, max(by_time, by_memory)))


def _is_pdf(path: Path) -> bool:
    return path.suffix.lower() == ".pdf"


def large_in_plan(plan: BatchPlan) -> tuple[tuple[Path, int], ...]:
    """PDFs warned about the time limit, or left out for memory: (path, recommended parts)."""
    found: dict[Path, int] = {}
    for warning in plan.warnings:
        if warning.item.detection.format is FormatId.PDF:
            parts = recommended_parts(warning.estimated_seconds, warning.limit_seconds)
            found[warning.item.source] = parts
    for item in plan.skipped:
        if item.reason is SkipReason.TOO_MUCH_MEMORY and _is_pdf(item.path):
            memory = item.measured or 0.0
            found[item.path] = recommended_parts(memory=memory, memory_limit=item.limit or 1.0)
    return tuple(found.items())


def large_in_report(report: BatchReport) -> tuple[tuple[Path, int], ...]:
    """PDFs stopped at a limit. It went past the limit, so at least twice the limit is assumed."""
    found: dict[Path, int] = {}
    for outcome in report.outcomes:
        item = outcome.item
        stopped = outcome.status is OutcomeStatus.STOPPED and item.split is None  # not a part
        if not stopped or item.detection.format is not FormatId.PDF:
            continue
        limit = outcome.limit or 1.0
        if outcome.error is ErrorCode.OUT_OF_MEMORY:
            found[item.source] = recommended_parts(memory=2 * limit, memory_limit=limit)
        else:
            found[item.source] = recommended_parts(max(item.cost, 2 * limit), limit)
    return tuple(found.items())


def most_parts(found: Sequence[tuple[Path, int]]) -> int:
    """One cut for them all: the largest recommendation."""
    return max((parts for _, parts in found), default=FEWEST)
