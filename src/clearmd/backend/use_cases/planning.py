"""Build the batch plan before writing anything (ADR-0010).

Thin path of slice A: input files only. Folders and the safety skips arrive in T08, the
archive check in T09, names and order in T11-T12.
"""

from collections.abc import Callable, Sequence
from pathlib import Path

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.events import BatchEvent, PlanReady
from clearmd.backend.schemas.limits import Limits
from clearmd.backend.schemas.models import (
    BatchPlan,
    InputError,
    InputProblem,
    PlannedConversion,
    SkippedItem,
)
from clearmd.backend.use_cases.paths import output_root_for, target_for
from clearmd.backend.use_cases.ports import FormatDetector


def build_plan(
    inputs: Sequence[Path],
    *,
    detector: FormatDetector,
    limits: Limits,
    output_root: Path | None = None,
    on_event: Callable[[BatchEvent], None] | None = None,
) -> BatchPlan:
    conversions: list[PlannedConversion] = []
    skipped: list[SkippedItem] = []
    errors: list[InputError] = []
    for source in inputs:
        if not source.exists():
            errors.append(InputError(source, InputProblem.NOT_FOUND))
            continue
        detection = detector.detect(source)
        if detection is None:
            skipped.append(SkippedItem(source, SkipReason.UNSUPPORTED_FORMAT))
            continue
        root = output_root_for(source, is_dir=False, override=output_root)
        target = target_for(source, root)
        conversions.append(
            PlannedConversion(
                source=source,
                output_root=root,
                target=target,
                detection=detection,
                exists=target.exists(),
                cost=limits.estimated_seconds(detection.format, source.stat().st_size),
            )
        )
    plan = BatchPlan(tuple(conversions), tuple(skipped), tuple(errors))
    if on_event is not None:
        on_event(PlanReady(plan))
    return plan
