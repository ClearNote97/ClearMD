"""Build the batch plan before writing anything (ADR-0010).

Scanning (T08) and the archive check (T09) feed it; names are resolved before anything is marked
as existing (T11); files that cannot fit in memory are skipped and the slow ones warned about, then
the plan is put in cost order (T12).
"""

from collections.abc import Callable, Sequence
from dataclasses import replace
from pathlib import Path

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.events import BatchEvent, PlanReady
from clearmd.backend.schemas.formats import WITH_STRATEGIES, ZIP_BASED, FormatId, Strategy
from clearmd.backend.schemas.limits import Limits
from clearmd.backend.schemas.models import (
    BatchPlan,
    Detection,
    PlannedConversion,
    PlanWarning,
    SkippedItem,
)
from clearmd.backend.use_cases.archive import inspect_archive, unsafe_reason
from clearmd.backend.use_cases.paths import (
    NameRequest,
    keeps_output_inside,
    output_root_for,
    resolve_names,
    target_for,
)
from clearmd.backend.use_cases.ports import FormatDetector
from clearmd.backend.use_cases.scanning import Candidate, scan
from clearmd.backend.use_cases.scheduling import order_by_cost


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


def build_plan(
    inputs: Sequence[Path],
    *,
    detector: FormatDetector,
    limits: Limits,
    recursive: bool = True,
    output_root: Path | None = None,
    on_event: Callable[[BatchEvent], None] | None = None,
    html_strategy: Strategy = Strategy.FULL,
) -> BatchPlan:
    unique_inputs = list(dict.fromkeys(inputs))  # "a.pdf a.pdf" is one file, converted once
    scanned = scan(unique_inputs, recursive=recursive, limits=limits, on_progress=on_event)
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
    for candidate in scanned.candidates:
        root = output_root_for(candidate.input, is_dir=candidate.input_is_dir, override=output_root)
        detection = detector.detect(candidate.path)
        if detection is None:
            skipped.append(
                SkippedItem(candidate.path, SkipReason.UNSUPPORTED_FORMAT, output_root=root)
            )
            continue
        size = memory_size = candidate.size
        if detection.format in ZIP_BASED:
            archive = inspect_archive(candidate.path, limits.max_zip_entries)
            if archive is not None:
                unsafe = unsafe_reason(archive, limits)
                if unsafe is not None:
                    reason, measured, limit = unsafe
                    skipped.append(
                        SkippedItem(
                            candidate.path, reason, measured=measured, limit=limit, output_root=root
                        )
                    )
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
            skipped.append(
                SkippedItem(
                    candidate.path,
                    SkipReason.TOO_MUCH_MEMORY_FOR_ARTICLE
                    if article
                    else SkipReason.TOO_MUCH_MEMORY,
                    measured=needed,
                    limit=limits.worker_memory,
                    output_root=root,
                )
            )
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
        )
        for (candidate, detection, root, cost, strategy), target in zip(
            drafts, resolve_names(requests), strict=True
        )
    ]
    ordered = order_by_cost(conversions)
    warnings = tuple(
        PlanWarning(item, item.cost, limits.time_per_file)
        for item in ordered
        if item.cost > limits.time_per_file
    )
    plan = BatchPlan(ordered, tuple(skipped), scanned.input_errors, warnings)
    if on_event is not None:
        on_event(PlanReady(plan))
    return plan
