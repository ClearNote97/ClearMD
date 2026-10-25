"""The facade every interface calls (ADR-0014): plan a batch, then run it."""

import os
from collections.abc import Callable, Sequence
from pathlib import Path

from clearmd.backend.api import composition
from clearmd.backend.schemas.events import BatchEvent
from clearmd.backend.schemas.models import BatchPlan, BatchReport, PlannedConversion
from clearmd.backend.use_cases.cancel import CancelToken
from clearmd.backend.use_cases.execution import execute_plan
from clearmd.backend.use_cases.planning import build_plan
from clearmd.backend.use_cases.reporting import by_output_root

__all__ = ["CancelToken", "plan_batch", "run_batch"]


def _ignore(event: BatchEvent) -> None:
    pass


def plan_batch(
    inputs: Sequence[Path],
    *,
    recursive: bool = True,
    output_root: Path | None = None,
    on_event: Callable[[BatchEvent], None] | None = None,
) -> BatchPlan:
    """Everything that would happen, computed without writing anything.

    The worker starts only if a file needs detection by content.
    """
    limits = composition.default_limits()
    worker = composition.build_runner(limits)
    try:
        return build_plan(
            # Absolute, without resolving symlinks: a link given as input must stay a link.
            [Path(os.path.abspath(path.expanduser())) for path in inputs],
            detector=composition.build_detector(worker),
            limits=limits,
            recursive=recursive,
            output_root=Path(os.path.abspath(output_root.expanduser())) if output_root else None,
            on_event=on_event,
        )
    finally:
        worker.close()


def run_batch(
    plan: BatchPlan,
    *,
    overwrite: Callable[[PlannedConversion], bool],
    on_event: Callable[[BatchEvent], None] | None = None,
    cancel: CancelToken | None = None,
    language: str = "en",
) -> BatchReport:
    """Convert every planned file in the worker process, write the results and, in each
    ClearMD_Output folder, its Resumen_ClearMD.md (also when the batch was cancelled)."""
    runner = composition.build_runner(composition.default_limits())
    try:
        report = execute_plan(
            plan,
            overwrite=overwrite,
            runner=runner,
            on_event=on_event or _ignore,
            cancel=cancel or CancelToken(),
            clock=composition.build_clock(),
            startup_seconds=composition.default_limits().worker_startup_seconds,
        )
    finally:
        runner.close()
    writer = composition.build_summary_writer(language)
    for root_report in by_output_root(report):
        try:
            writer.write(root_report)
        except OSError:
            pass  # an unwritable root: its files already failed with permission_denied
    return report
