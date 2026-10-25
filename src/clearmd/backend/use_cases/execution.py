"""Execute a confirmed plan: one file at a time through the runner, atomic writes (ADR-0013).

A failure never stops the batch. An output root that cannot be written fails its files without
converting them (AC-27); time and memory limits give a "stopped" outcome, not a failure (AC-44).
"""

import os
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from clearmd.backend.schemas.errors import Cancelled, ConversionError, ErrorCode
from clearmd.backend.schemas.events import BatchEvent, ConversionFinished, ConversionStarted
from clearmd.backend.schemas.formats import RESULTS_DIR_NAME, TEMP_SUFFIX
from clearmd.backend.schemas.models import (
    BatchPlan,
    BatchReport,
    ConversionOutcome,
    OutcomeStatus,
    PlannedConversion,
)
from clearmd.backend.use_cases.cancel import CancelToken
from clearmd.backend.use_cases.estimation import TimeLeft
from clearmd.backend.use_cases.ports import Clock, ConversionRunner

STOPPING_CODES = frozenset({ErrorCode.TIMED_OUT, ErrorCode.OUT_OF_MEMORY})


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


def _denied(item: PlannedConversion, detail: str) -> ConversionOutcome:
    return ConversionOutcome(item, OutcomeStatus.FAILED, ErrorCode.PERMISSION_DENIED, detail)


def _write_problem(output_root: Path) -> str | None:
    """``None`` if the results folder can be created, else the technical detail."""
    try:
        (output_root / RESULTS_DIR_NAME).mkdir(parents=True, exist_ok=True)
    except PermissionError as error:
        return str(error)
    return None


def _convert_one(
    item: PlannedConversion, runner: ConversionRunner, cancel: CancelToken
) -> ConversionOutcome:
    try:
        markdown = runner.convert(item, cancel)
        atomic_write(item.target, markdown)
    except ConversionError as error:
        status = OutcomeStatus.STOPPED if error.code in STOPPING_CODES else OutcomeStatus.FAILED
        return ConversionOutcome(item, status, error.code, error.detail)
    except PermissionError as error:
        return _denied(item, str(error))
    return ConversionOutcome(item, OutcomeStatus.CONVERTED)


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
    if plan.conversions and not cancel.is_set():
        try:
            runner.warm_up(cancel)
        except Cancelled:
            pass  # every file is reported as cancelled below
        except ConversionError:
            pass  # a worker that cannot start fails each file with its own error below
    outcomes: list[ConversionOutcome] = []
    total = len(plan.conversions)
    estimate = TimeLeft(startup_seconds=startup_seconds)
    checked_roots: set[Path] = set()
    denied_roots: dict[Path, str] = {}
    for index, item in enumerate(plan.conversions, start=1):
        if cancel.is_set():
            outcomes.append(ConversionOutcome(item, OutcomeStatus.CANCELLED))
            continue
        if item.output_root not in checked_roots:
            checked_roots.add(item.output_root)
            problem = _write_problem(item.output_root)
            if problem is not None:
                denied_roots[item.output_root] = problem
        if item.output_root in denied_roots:
            outcome = _denied(item, denied_roots[item.output_root])
        # Re-checked now: an output may have appeared after the plan was made.
        elif (item.exists or item.target.exists()) and not overwrite(item):
            outcome = ConversionOutcome(item, OutcomeStatus.KEPT)
        else:
            pending = (pending.cost for pending in plan.conversions[index - 1 :])
            seconds_left = estimate.seconds_left(pending) if outcomes else None
            on_event(ConversionStarted(index, total, item, seconds_left))
            began = clock.now()
            try:
                outcome = _convert_one(item, runner, cancel)
            except Cancelled:
                outcome = ConversionOutcome(item, OutcomeStatus.CANCELLED)
            seconds = (clock.now() - began).total_seconds()
            outcome = replace(outcome, seconds=seconds)
            estimate.record(estimated=item.cost, measured=seconds)
            if outcome.error is ErrorCode.PERMISSION_DENIED:
                denied_roots[item.output_root] = outcome.detail
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
