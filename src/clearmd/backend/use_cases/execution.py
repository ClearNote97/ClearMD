"""Execute a confirmed plan: one file at a time through the runner, safe atomic writes (ADR-0013).

A failure never stops the batch. An output root that cannot be created fails its files without
converting them (AC-27); a result that cannot be saved fails only that file; time and memory limits
give a "stopped" outcome, not a failure (AC-44).
"""

import errno
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from clearmd.backend.schemas.errors import Cancelled, ConversionError, ErrorCode
from clearmd.backend.schemas.events import BatchEvent, ConversionFinished, ConversionStarted
from clearmd.backend.schemas.models import (
    BatchPlan,
    BatchReport,
    ConversionOutcome,
    OutcomeStatus,
    PlannedConversion,
)
from clearmd.backend.use_cases.cancel import CancelToken
from clearmd.backend.use_cases.estimation import TimeLeft
from clearmd.backend.use_cases.output_files import (
    UnsafeOutput,
    atomic_write,
    prepare_root,
    sweep_temporary_files,
)
from clearmd.backend.use_cases.ports import Clock, ConversionRunner

STOPPING_CODES = frozenset({ErrorCode.TIMED_OUT, ErrorCode.OUT_OF_MEMORY})
# Errors that mean "this folder cannot be written at all" rather than "this file failed".
_NOT_WRITABLE = frozenset({errno.EACCES, errno.EPERM, errno.EROFS})


def _describe(error: BaseException) -> str:
    return f"{type(error).__name__}: {error}"


def _root_problem(output_root: Path) -> tuple[ErrorCode, str] | None:
    """``None`` if the output root is ready; else why its files cannot be written."""
    try:
        prepare_root(output_root)
        sweep_temporary_files(output_root)
    except UnsafeOutput as error:
        return ErrorCode.WRITE_FAILED, _describe(error)
    except OSError as error:
        not_writable = isinstance(error, PermissionError) or error.errno in _NOT_WRITABLE
        code = ErrorCode.PERMISSION_DENIED if not_writable else ErrorCode.WRITE_FAILED
        return code, _describe(error)
    return None


def _convert_one(
    item: PlannedConversion, runner: ConversionRunner, cancel: CancelToken
) -> ConversionOutcome:
    try:
        result = runner.convert(item, cancel)
    except ConversionError as error:
        status = OutcomeStatus.STOPPED if error.code in STOPPING_CODES else OutcomeStatus.FAILED
        return ConversionOutcome(item, status, error.code, error.detail, limit=error.limit)
    try:
        atomic_write(item.target, result.markdown, inside=item.output_root)
    except OSError as error:  # this file only: disk full, name too long, locked, a folder...
        return ConversionOutcome(
            item, OutcomeStatus.FAILED, ErrorCode.WRITE_FAILED, _describe(error)
        )
    return ConversionOutcome(item, OutcomeStatus.CONVERTED, notes=result.notes)


def execute_plan(
    plan: BatchPlan,
    *,
    overwrite: Callable[[PlannedConversion], bool],
    runner: ConversionRunner,
    on_event: Callable[[BatchEvent], None],
    cancel: CancelToken,
    clock: Clock,
    startup_seconds: float = 0.0,
) -> BatchReport:
    started_at = clock.now()
    outcomes: list[ConversionOutcome] = []
    total = len(plan.conversions)
    estimate = TimeLeft(startup_seconds=startup_seconds)
    root_problems: dict[Path, tuple[ErrorCode, str] | None] = {}
    startup_failure: ConversionError | None = None
    for index, item in enumerate(plan.conversions, start=1):
        if cancel.is_set():
            outcomes.append(ConversionOutcome(item, OutcomeStatus.CANCELLED))
            continue
        if item.output_root not in root_problems:
            root_problems[item.output_root] = _root_problem(item.output_root)
        problem = root_problems[item.output_root]
        if problem is not None:
            outcome = ConversionOutcome(item, OutcomeStatus.FAILED, *problem)
        # Re-checked now: an output may have appeared after the plan was made.
        elif (item.exists or item.target.exists()) and not overwrite(item):
            outcome = ConversionOutcome(item, OutcomeStatus.KEPT)
        elif startup_failure is not None:  # do not wait for a worker that cannot start
            outcome = ConversionOutcome(
                item, OutcomeStatus.FAILED, startup_failure.code, startup_failure.detail
            )
        else:
            outcome = _timed_conversion(
                item, runner, cancel, clock, estimate, plan, index, total, on_event, bool(outcomes)
            )
            if outcome.error is ErrorCode.WORKER_CRASHED and "not ready" in outcome.detail:
                startup_failure = ConversionError(outcome.error, outcome.detail)
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


def _timed_conversion(
    item: PlannedConversion,
    runner: ConversionRunner,
    cancel: CancelToken,
    clock: Clock,
    estimate: TimeLeft,
    plan: BatchPlan,
    index: int,
    total: int,
    on_event: Callable[[BatchEvent], None],
    has_previous: bool,
) -> ConversionOutcome:
    """Convert one file; its time never includes starting a (new) worker (AC-41)."""
    try:
        runner.warm_up(cancel)
    except Cancelled:
        return ConversionOutcome(item, OutcomeStatus.CANCELLED)
    except ConversionError as error:
        return ConversionOutcome(item, OutcomeStatus.FAILED, error.code, error.detail)
    pending = (pending.cost for pending in plan.conversions[index - 1 :])
    seconds_left = estimate.seconds_left(pending) if has_previous else None
    on_event(ConversionStarted(index, total, item, seconds_left))
    began = clock.now()
    try:
        outcome = _convert_one(item, runner, cancel)
    except Cancelled:
        outcome = ConversionOutcome(item, OutcomeStatus.CANCELLED)
    seconds = (clock.now() - began).total_seconds()
    estimate.record(estimated=item.cost, measured=seconds)
    return replace(outcome, seconds=seconds)
