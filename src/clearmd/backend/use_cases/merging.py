"""Merge the planned documents into one file (feature 026, ADR-0046).

Into Markdown: each document is converted as Convert converts it, each with its own time limit
(a Markdown file is read as it is); the texts are joined in the list's order, each after a
comment naming its source and a visible line ("Document 2 of 3: b.pdf"). Into PDF: the PDFs'
pages are copied whole, in order, in the worker. A document that fails is left out and told;
fewer than two documents write nothing. A merged file never replaces another: "(2)" is added
(audit 2026-11-08).
"""

import os
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from clearmd.backend.schemas.errors import Cancelled, ConversionError, ErrorCode, SkipReason
from clearmd.backend.schemas.events import BatchEvent, ConversionFinished, ConversionStarted
from clearmd.backend.schemas.formats import MERGE_DIR_NAME, FormatId
from clearmd.backend.schemas.merge import Into, MergeSpec
from clearmd.backend.schemas.models import (
    BatchPlan,
    BatchReport,
    ConversionOutcome,
    Detection,
    OutcomeStatus,
    PlannedConversion,
)
from clearmd.backend.use_cases.cancel import CancelToken
from clearmd.backend.use_cases.output_files import atomic_write, atomic_write_bytes, prepare_root
from clearmd.backend.use_cases.ports import Clock, ConversionRunner, PageCutter
from clearmd.backend.use_cases.relink import relinked

STOPPING = frozenset({ErrorCode.TIMED_OUT, ErrorCode.OUT_OF_MEMORY})


def as_merge(plan: BatchPlan, into: Into, stamp: str) -> BatchPlan:
    """A plan made to merge (already in the list's order): one output folder, the first
    document's, and every document's target the merged file."""
    if not plan.conversions:
        return replace(plan, merge=MergeSpec(into, stamp=stamp))
    root = plan.conversions[0].output_root
    target = root / MERGE_DIR_NAME / f"{stamp}{into.suffix}"
    items = tuple(
        replace(item, output_root=root, target=target, exists=False, images="")
        for item in plan.conversions
    )
    by_source = {item.source: item for item in items}
    warnings = tuple(replace(w, item=by_source[w.item.source]) for w in plan.warnings)
    return replace(plan, conversions=items, warnings=warnings, merge=MergeSpec(into, target, stamp))


def merge_skip(detection: Detection, merge: Into | None) -> SkipReason | None:
    """Why a file is left out of a merge: one PDF is made of PDFs only."""
    if merge is Into.PDF and detection.format is not FormatId.PDF:
        return SkipReason.NOT_FOR_PDF_MERGE
    return None


def source_marker(item: PlannedConversion) -> str:
    """Where each document starts: a comment a Markdown viewer does not show."""
    name = item.source.name.replace("--", "- -")  # "--" would end the comment early
    return f"<!-- ClearMD: {name} -->\n\n"


def heading(spec: MergeSpec, index: int, total: int, item: PlannedConversion) -> str:
    """The visible line that opens a document in a merged Markdown, in italics."""
    name = item.source.name.replace("*", "\\*")
    return "*" + spec.heading.format(index=index, total=total, name=name) + "*\n\n"


def free_target(target: Path) -> Path:
    """``target``, or "name (2).md", "name (3).md"... when a file is already there."""
    candidate, number = target, 1
    while os.path.lexists(candidate):
        number += 1
        candidate = target.with_name(f"{target.stem} ({number}){target.suffix}")
    return candidate


def _failed(item: PlannedConversion, error: ConversionError) -> ConversionOutcome:
    status = OutcomeStatus.STOPPED if error.code in STOPPING else OutcomeStatus.FAILED
    return ConversionOutcome(item, status, error.code, error.detail, limit=error.limit)


def _piece(
    item: PlannedConversion, runner: ConversionRunner, cutter: PageCutter, cancel: CancelToken
) -> str:
    if item.detection.format is FormatId.MARKDOWN:
        text = cutter.read_text(item, cancel)
    else:
        text = runner.convert(item, cancel).markdown
    return relinked(text, item.source.parent, item.target.parent)  # images show from OutputUnif


def execute_merge(
    plan: BatchPlan,
    *,
    runner: ConversionRunner,
    cutter: PageCutter,
    on_event: Callable[[BatchEvent], None],
    cancel: CancelToken,
    clock: Clock,
) -> BatchReport:
    started_at = clock.now()
    spec = plan.merge
    assert spec is not None
    total = len(plan.conversions)
    outcomes: list[ConversionOutcome] = []
    pieces: list[tuple[PlannedConversion, str]] = []
    for index, item in enumerate(plan.conversions, start=1):
        if cancel.is_set():
            outcomes.append(ConversionOutcome(item, OutcomeStatus.CANCELLED))
            continue
        on_event(ConversionStarted(index, total, item, None))
        began = clock.now()
        try:
            if spec.into is Into.PDF:
                cutter.count_pages(item, cancel)  # opens: a broken or locked PDF fails here
                pieces.append((item, ""))
            else:
                pieces.append((item, _piece(item, runner, cutter, cancel)))
            outcome = ConversionOutcome(item, OutcomeStatus.CONVERTED)
        except Cancelled:
            outcome = ConversionOutcome(item, OutcomeStatus.CANCELLED)
        except ConversionError as error:
            outcome = _failed(item, error)
        outcome = replace(outcome, seconds=(clock.now() - began).total_seconds())
        outcomes.append(outcome)
        on_event(ConversionFinished(index, total, outcome))
    outcomes = _write(plan, pieces, outcomes, cutter, cancel)
    return BatchReport(
        started_at=started_at,
        finished_at=clock.now(),
        outcomes=tuple(outcomes),
        skipped=plan.skipped,
        input_errors=plan.input_errors,
        cancelled=cancel.is_set(),
    )


def _write(
    plan: BatchPlan,
    pieces: list[tuple[PlannedConversion, str]],
    outcomes: list[ConversionOutcome],
    cutter: PageCutter,
    cancel: CancelToken,
) -> list[ConversionOutcome]:
    """Write the merged file from the pieces; when it cannot be, the merged documents fail."""
    spec = plan.merge
    assert spec is not None
    joined = {item.source for item, _ in pieces}
    if not plan.conversions:
        return outcomes
    root = plan.conversions[0].output_root
    target = spec.target
    problem: tuple[ErrorCode, str] | None = None
    try:  # the folder always: the summary is written there even when nothing is merged (B4-01)
        prepare_root(root, MERGE_DIR_NAME)
        if cancel.is_set():
            return [  # a cancelled merge is told as cancelled, not as a failure (B1-07)
                replace(outcome, status=OutcomeStatus.CANCELLED)
                if outcome.status is OutcomeStatus.CONVERTED
                else outcome
                for outcome in outcomes
            ]
        if len(pieces) < 2:
            problem = (ErrorCode.NOTHING_TO_MERGE, f"{len(pieces)} document(s) to merge")
        else:
            target = free_target(spec.target)
            if spec.into is Into.PDF:
                data = cutter.merge_pdfs([item for item, _ in pieces], cancel)
                atomic_write_bytes(target, data, inside=root)
            else:
                total = len(pieces)
                text = "\n\n---\n\n".join(
                    source_marker(item) + heading(spec, index, total, item) + piece.strip("\n")
                    for index, (item, piece) in enumerate(pieces, start=1)
                )
                atomic_write(target, text + "\n", inside=root)
    except Cancelled:  # during the last step, too: cancelled, never an error (audit v2, B1-03)
        return [
            replace(outcome, status=OutcomeStatus.CANCELLED)
            if outcome.status is OutcomeStatus.CONVERTED
            else outcome
            for outcome in outcomes
        ]
    except ConversionError as error:
        problem = (error.code, error.detail)
    except OSError as error:
        problem = (ErrorCode.WRITE_FAILED, f"{type(error).__name__}: {error}")
    if problem is None:
        return [
            replace(outcome, item=replace(outcome.item, target=target))
            if outcome.item.source in joined
            else outcome
            for outcome in outcomes
        ]
    return [  # every document gets the reason: the ones joined, and the ones that were fine
        replace(outcome, status=OutcomeStatus.FAILED, error=problem[0], detail=problem[1])
        if outcome.status is OutcomeStatus.CONVERTED
        else outcome
        for outcome in outcomes
    ]
