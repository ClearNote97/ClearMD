"""Build the batch plan before writing anything (ADR-0010).

Scanning (T08) and the archive check (T09) feed it; names are resolved before anything is marked
as existing (T11); the order and the warnings come in T12.
"""

from collections.abc import Callable, Sequence
from pathlib import Path

from clearmd.backend.schemas.errors import SkipReason
from clearmd.backend.schemas.events import BatchEvent, PlanReady
from clearmd.backend.schemas.formats import ZIP_BASED
from clearmd.backend.schemas.limits import Limits
from clearmd.backend.schemas.models import BatchPlan, Detection, PlannedConversion, SkippedItem
from clearmd.backend.use_cases.archive import inspect_archive, is_unsafe
from clearmd.backend.use_cases.paths import (
    NameRequest,
    keeps_output_inside,
    output_root_for,
    resolve_names,
    target_for,
)
from clearmd.backend.use_cases.ports import FormatDetector
from clearmd.backend.use_cases.scanning import Candidate, scan


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
) -> BatchPlan:
    scanned = scan(inputs, recursive=recursive, limits=limits, on_progress=on_event)
    drafts: list[tuple[Candidate, Detection, Path, float]] = []
    requests: list[NameRequest] = []
    skipped: list[SkippedItem] = list(scanned.skipped)
    for candidate in scanned.candidates:
        detection = detector.detect(candidate.path)
        if detection is None:
            skipped.append(SkippedItem(candidate.path, SkipReason.UNSUPPORTED_FORMAT))
            continue
        size = candidate.size
        if detection.format in ZIP_BASED:
            archive = inspect_archive(candidate.path)
            if archive is not None:
                if is_unsafe(archive, limits):
                    skipped.append(SkippedItem(candidate.path, SkipReason.UNSAFE_ARCHIVE))
                    continue
                size = archive.text_bytes
        root = output_root_for(candidate.input, is_dir=candidate.input_is_dir, override=output_root)
        target = target_for(candidate.path, root, _relative_dir(candidate))
        drafts.append(
            (candidate, detection, root, limits.estimated_seconds(detection.format, size))
        )
        requests.append(NameRequest(candidate.path, target, _label(candidate, detection)))
    conversions = [
        PlannedConversion(
            source=candidate.path,
            output_root=root,
            target=target,
            detection=detection,
            exists=target.exists(),
            cost=cost,
        )
        for (candidate, detection, root, cost), target in zip(
            drafts, resolve_names(requests), strict=True
        )
    ]
    plan = BatchPlan(tuple(conversions), tuple(skipped), scanned.input_errors)
    if on_event is not None:
        on_event(PlanReady(plan))
    return plan
