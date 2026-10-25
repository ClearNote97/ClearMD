"""Execute a confirmed plan: one file at a time through the runner, atomic writes (ADR-0013)."""

import os
from collections.abc import Callable
from pathlib import Path

from clearmd.backend.schemas.errors import Cancelled, ConversionError, ErrorCode
from clearmd.backend.schemas.events import BatchEvent, ConversionFinished, ConversionStarted
from clearmd.backend.schemas.formats import TEMP_SUFFIX
from clearmd.backend.schemas.models import (
    BatchPlan,
    BatchReport,
    ConversionOutcome,
    OutcomeStatus,
    PlannedConversion,
)
from clearmd.backend.use_cases.cancel import CancelToken
from clearmd.backend.use_cases.ports import Clock, ConversionRunner


def atomic_write(target: Path, text: str) -> None:
    """Write UTF-8 with LF line endings; a reader never sees a half-written file."""
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + TEMP_SUFFIX)
    try:
        temporary.write_bytes(text.replace("\r\n", "\n").encode("utf-8"))
        os.replace(temporary, target)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _convert_one(
    item: PlannedConversion, runner: ConversionRunner, cancel: CancelToken
) -> ConversionOutcome:
    try:
        markdown = runner.convert(item, cancel)
        atomic_write(item.target, markdown)
    except ConversionError as error:
        return ConversionOutcome(item, OutcomeStatus.FAILED, error.code, error.detail)
    except PermissionError as error:
        return ConversionOutcome(
            item, OutcomeStatus.FAILED, ErrorCode.PERMISSION_DENIED, str(error)
        )
    return ConversionOutcome(item, OutcomeStatus.CONVERTED)


def execute_plan(
    plan: BatchPlan,
    *,
    overwrite: Callable[[PlannedConversion], bool],
    runner: ConversionRunner,
    on_event: Callable[[BatchEvent], None],
    cancel: CancelToken,
    clock: Clock,
) -> BatchReport:
    started_at = clock.now()
    outcomes: list[ConversionOutcome] = []
    total = len(plan.conversions)
    for index, item in enumerate(plan.conversions, start=1):
        if cancel.is_set():
            outcomes.append(ConversionOutcome(item, OutcomeStatus.CANCELLED))
            continue
        if item.exists and not overwrite(item):
            outcome = ConversionOutcome(item, OutcomeStatus.KEPT)
        else:
            on_event(ConversionStarted(index, total, item))
            try:
                outcome = _convert_one(item, runner, cancel)
            except Cancelled:
                outcome = ConversionOutcome(item, OutcomeStatus.CANCELLED)
        outcomes.append(outcome)
        on_event(ConversionFinished(index, total, outcome))
    return BatchReport(
        started_at=started_at,
        finished_at=clock.now(),
        outcomes=tuple(outcomes),
        skipped=plan.skipped,
        input_errors=plan.input_errors,
        cancelled=cancel.is_set(),
    )
