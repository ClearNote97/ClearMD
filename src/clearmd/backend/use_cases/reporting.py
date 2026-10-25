"""Split a batch report into one report per ClearMD_Output folder (ADR-0016, AC-22/28)."""

from pathlib import Path

from clearmd.backend.schemas.models import (
    BatchReport,
    ConversionOutcome,
    OutputRootReport,
    SkippedItem,
)


def by_output_root(report: BatchReport) -> tuple[OutputRootReport, ...]:
    """Only roots that had planned conversions get a summary: nothing planned, nothing written."""
    outcomes: dict[Path, list[ConversionOutcome]] = {}
    for outcome in report.outcomes:
        outcomes.setdefault(outcome.item.output_root, []).append(outcome)
    skipped: dict[Path, list[SkippedItem]] = {}
    for item in report.skipped:
        if item.output_root in outcomes:
            skipped.setdefault(item.output_root, []).append(item)
    return tuple(
        OutputRootReport(
            root=root,
            started_at=report.started_at,
            finished_at=report.finished_at,
            outcomes=tuple(root_outcomes),
            skipped=tuple(skipped.get(root, ())),
            cancelled=report.cancelled,
        )
        for root, root_outcomes in outcomes.items()
    )
