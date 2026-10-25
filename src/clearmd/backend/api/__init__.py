"""The facade every interface calls (ADR-0014): plan a batch, then run it."""

from collections.abc import Callable, Sequence
from pathlib import Path

from clearmd.backend.api import composition
from clearmd.backend.schemas.events import BatchEvent
from clearmd.backend.schemas.models import BatchPlan, BatchReport, PlannedConversion
from clearmd.backend.use_cases.cancel import CancelToken
from clearmd.backend.use_cases.execution import execute_plan
from clearmd.backend.use_cases.planning import build_plan

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
    """Everything that would happen, computed without writing anything."""
    return build_plan(
        inputs,
        detector=composition.build_detector(),
        limits=composition.default_limits(),
        recursive=recursive,
        output_root=output_root,
        on_event=on_event,
    )


def run_batch(
    plan: BatchPlan,
    *,
    overwrite: Callable[[PlannedConversion], bool],
    on_event: Callable[[BatchEvent], None] | None = None,
    cancel: CancelToken | None = None,
) -> BatchReport:
    """Convert every planned file in the worker process and write the results."""
    runner = composition.build_runner(composition.default_limits())
    try:
        return execute_plan(
            plan,
            overwrite=overwrite,
            runner=runner,
            on_event=on_event or _ignore,
            cancel=cancel or CancelToken(),
            clock=composition.build_clock(),
        )
    finally:
        runner.close()
