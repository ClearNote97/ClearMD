"""Build the batch plan before writing anything (ADR-0010).

Scanning (T08) and the archive check (T09) feed it; names are resolved before anything is marked
as existing (T11); files that cannot fit in memory are skipped and the slow ones warned about, then
the plan is put in cost order (T12).
"""

from collections.abc import Callable, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.events import BatchEvent, PlanReady
from clearmd.backend.schemas.formats import WITH_STRATEGIES, ZIP_BASED, FormatId, Strategy
from clearmd.backend.schemas.limits import Limits
from clearmd.backend.schemas.merge import Into
from clearmd.backend.schemas.models import (
    BatchPlan,
    Detection,
    PlannedConversion,
    PlanWarning,
    SkippedItem,
)
from clearmd.backend.schemas.split import SplitSpec
from clearmd.backend.use_cases.archive import inspect_archive, unsafe_reason
from clearmd.backend.use_cases.cancel import CancelToken
from clearmd.backend.use_cases.merging import as_merge, merge_skip
from clearmd.backend.use_cases.paths import (
    NameRequest,
    keeps_output_inside,
    output_root_for,
    resolve_names,
    split_target_for,
    target_for,
)
from clearmd.backend.use_cases.ports import FormatDetector
from clearmd.backend.use_cases.scanning import Candidate, first_time, scan, unsupported_reason
from clearmd.backend.use_cases.scheduling import order_by_cost
from clearmd.backend.use_cases.splitting import (
    split_cost,
    split_detection,
    split_memory,
    split_skip,
)


def _relative_dir(candidate: Candidate) -> Path:
    """A folder input keeps its own name (``P/project/sub/a.pdf`` → ``project/sub``), except a drive
    root or the home folder, whose contents go directly into OutputMD (ADR-0016)."""
    if not candidate.input_is_dir:
        return Path()
    if keeps_output_inside(candidate.input):
        return candidate.relative_dir
    return Path(candidate.input.name) / candidate.relative_dir


def _label(candidate: Candidate, detection: Detection) -> str:
    return candidate.path.suffix.lstrip(".").lower() or detection.format.value


def item_left_out(
    candidate: Candidate,
    reason: SkipReason,
    root: Path,
    measured: tuple[float, float] | None = None,
) -> SkippedItem:
    """A file left out; ``measured``: what it needs and the limit, when a limit left it out."""
    needed, limit = measured if measured is not None else (None, None)
    return SkippedItem(
        candidate.path, reason, measured=needed, limit=limit, output_root=root, **_found(candidate)
    )


def _found(candidate: Candidate) -> dict[str, Any]:
    """Where a file left out was found: its summary places it as its results would have been."""
    return {"input": candidate.input, "input_is_dir": candidate.input_is_dir}


def build_plan(
    inputs: Sequence[Path],
    *,
    detector: FormatDetector,
    limits: Limits,
    recursive: bool = True,
    output_root: Path | None = None,
    on_event: Callable[[BatchEvent], None] | None = None,
    html_strategy: Strategy = Strategy.FULL,
    cancel: CancelToken | None = None,
    split: SplitSpec | None = None,
    merge: Into | None = None,
    stamp: str = "",
) -> BatchPlan:
    """The plan; with ``split``, of the PDFs to split (feature 023): any other file is left out,
    and the parts' folder in OutputSep is the target."""
    unique_inputs = list(dict.fromkeys(inputs))  # "a.pdf a.pdf" is one file, converted once
    scanned = scan(
        unique_inputs,
        recursive=recursive,
        limits=limits,
        on_progress=on_event,
        cancel=cancel,
        markdown=split is not None or merge is not None,  # Split and Merge take Markdown
    )
    drafts: list[tuple[Candidate, Detection, Path, float, Strategy]] = []
    requests: list[NameRequest] = []
    skipped: list[SkippedItem] = [
        replace(
            item,
            output_root=output_root_for(item.input, is_dir=item.input_is_dir, override=output_root)
            if item.input is not None
            else None,
        )
        for item in scanned.skipped
    ]
    seen: set[str] = set()
    for candidate in scanned.candidates:
        if cancel is not None and cancel.is_set():  # cancelled: what is left is not examined
            break
        root = output_root_for(candidate.input, is_dir=candidate.input_is_dir, override=output_root)
        if not first_time(candidate.path, seen):
            skipped.append(item_left_out(candidate, SkipReason.ALREADY_INCLUDED, root))
            continue
        detection = split_detection(candidate.path) if split or merge else None
        detection = detection or detector.detect(candidate.path)
        if detection is None:
            skipped.append(item_left_out(candidate, unsupported_reason(candidate.path), root))
            continue
        reason = split_skip(detection, split) if split else merge_skip(detection, merge)
        if reason is not None:  # a tool that does not take it (features 023, 024, 026)
            skipped.append(item_left_out(candidate, reason, root))
            continue
        if split is not None:
            needed = split_memory(limits, detection.format, candidate.size)
            if needed is not None:  # an Excel workbook too heavy to cut (B2-01)
                memory = (needed, limits.worker_memory)
                skipped.append(item_left_out(candidate, SkipReason.TOO_MUCH_MEMORY, root, memory))
                continue
            cost = split_cost(limits, candidate.size, split, detection.format)
            target = split_target_for(candidate.path, root, _relative_dir(candidate))
            drafts.append((candidate, detection, root, cost, Strategy.FULL))
            requests.append(NameRequest(candidate.path, target, _label(candidate, detection)))
            continue
        size = memory_size = candidate.size
        if detection.format in ZIP_BASED:
            archive = inspect_archive(candidate.path, limits.max_zip_entries)
            if archive is not None:
                unsafe = unsafe_reason(archive, limits)
                if unsafe is not None:
                    reason, measured, limit = unsafe
                    skipped.append(item_left_out(candidate, reason, root, (measured, limit)))
                    continue
                size = archive.text_bytes
                # markitdown's docx pre-processing reads every entry into memory (review of 001).
                if detection.format is FormatId.DOCX:
                    memory_size = archive.uncompressed
        strategy = html_strategy if detection.format in WITH_STRATEGIES else Strategy.FULL
        needed = limits.estimated_memory(detection.format, memory_size, strategy)
        if needed > limits.worker_memory:
            # In article mode the reason says so, and what to do: --html full (ADR-0025: never
            # handed to markitdown behind the user's back, where the guarantee does not hold).
            article = strategy is not Strategy.FULL
            reason = (
                SkipReason.TOO_MUCH_MEMORY_FOR_ARTICLE if article else SkipReason.TOO_MUCH_MEMORY
            )
            memory = (needed, limits.worker_memory)
            skipped.append(item_left_out(candidate, reason, root, memory))
            continue
        target = target_for(candidate.path, root, _relative_dir(candidate))
        cost = limits.estimated_seconds(detection.format, size, strategy)
        drafts.append((candidate, detection, root, cost, strategy))
        requests.append(NameRequest(candidate.path, target, _label(candidate, detection)))
    conversions = [
        PlannedConversion(
            source=candidate.path,
            output_root=root,
            target=target,
            detection=detection,
            exists=target.exists(),
            cost=cost,
            strategy=strategy,
            split=split,
        )
        for (candidate, detection, root, cost, strategy), target in zip(
            drafts, resolve_names(requests), strict=True
        )
    ]
    ordered = tuple(conversions) if merge else order_by_cost(conversions)  # Merge: the list's order
    warnings = tuple(  # a split file is converted part by part: no file-wide warning
        PlanWarning(item, item.cost, limits.time_per_file)
        for item in ordered
        if item.cost > limits.time_per_file and item.split is None
    )
    plan = BatchPlan(ordered, tuple(skipped), scanned.input_errors, warnings)
    if merge is not None:
        plan = as_merge(plan, merge, stamp)
    if on_event is not None:
        on_event(PlanReady(plan))
    return plan
