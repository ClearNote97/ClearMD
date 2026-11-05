"""Results: the batch's rows and figures, and the folders that hold the converted files."""

from pathlib import Path

from clearmd.backend.schemas.models import BatchReport, OutcomeStatus


def result_folders(report: BatchReport | None) -> tuple[Path, ...]:
    """The ClearMD_Output folders that hold converted files (none before a batch)."""
    if report is None:
        return ()
    roots = dict.fromkeys(
        outcome.item.output_root
        for outcome in report.outcomes
        if outcome.status is OutcomeStatus.CONVERTED
    )
    return tuple(roots)
