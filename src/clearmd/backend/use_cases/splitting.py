"""Split one file into parts of whole pages (feature 023, ADR-0044).

The pages are counted and copied in the worker. Here: the cut, the parts' names, and writing
them. A part's Markdown is converted part by part, each within the time limit (ADR-0015).
Overwriting replaces only the parts of an earlier cut; other files in the folder stay.
"""

from dataclasses import replace
from pathlib import Path

from clearmd.backend.schemas.errors import ConversionError, ErrorCode, SkipReason
from clearmd.backend.schemas.formats import MARKDOWN_EXTENSIONS, FormatId, Strategy
from clearmd.backend.schemas.limits import Limits
from clearmd.backend.schemas.models import (
    ConversionOutcome,
    Detection,
    DetectionMethod,
    OutcomeStatus,
    PlannedConversion,
)
from clearmd.backend.schemas.notes import ConversionNote, NoteItem, NoteKind
from clearmd.backend.schemas.split import Cut, SplitSpec
from clearmd.backend.use_cases.cancel import CancelToken
from clearmd.backend.use_cases.output_files import (
    atomic_write,
    atomic_write_bytes,
    remove_regular_file,
)
from clearmd.backend.use_cases.part_stage import PartStage
from clearmd.backend.use_cases.ports import ConversionRunner, PageCutter
from clearmd.backend.use_cases.relink import relinked
from clearmd.backend.use_cases.split_formats import OWN_FORMAT_PARTS, split_file
from clearmd.backend.use_cases.split_names import part_name
from clearmd.backend.use_cases.split_notes import merged, over_size

STOPPING_CODES = frozenset({ErrorCode.TIMED_OUT, ErrorCode.OUT_OF_MEMORY})


def split_detection(path: Path) -> Detection | None:
    """Markdown, by its extension: it is only ever split, never converted (feature 024)."""
    if path.suffix.lower() in MARKDOWN_EXTENSIONS:
        return Detection(FormatId.MARKDOWN, DetectionMethod.EXTENSION)
    return None


def split_skip(detection: Detection, split: SplitSpec) -> SkipReason | None:
    """Why a file is left out of Split: a format it does not take, or a cut its format has not
    (features 023, 024, 027)."""
    if detection.format is FormatId.MARKDOWN:
        return SkipReason.CUT_NOT_FOR_MARKDOWN if split.cut is Cut.PAGES else None
    if detection.format is FormatId.XLSX:  # by whole sheets (feature 027)
        return None if split.cut is Cut.PARTS else SkipReason.CUT_BY_SHEETS
    if detection.format in OWN_FORMAT_PARTS:  # text and CSV have no pages (feature 027)
        return SkipReason.NO_PAGES_TO_CUT if split.cut is Cut.PAGES else None
    return None if detection.format is FormatId.PDF else SkipReason.NOT_SPLITTABLE


def split_cost(
    limits: Limits, size: int, split: SplitSpec, format_id: FormatId = FormatId.PDF
) -> float:
    """Each format's own cost (audit 2026-11-08, B2-01): copying pages or lines is quick and
    converting the parts costs what converting the file does; an Excel part loads the whole
    workbook, once per part."""
    whole = limits.estimated_seconds(format_id, size, Strategy.FULL)
    if format_id is FormatId.XLSX:
        parts = split.size if split.cut is Cut.PARTS else 1
        return whole * max(1, parts) + (whole if split.keep.markdown else 0)
    return whole / 20 + (whole if split.keep.markdown else 0)


def split_memory(limits: Limits, format_id: FormatId, size: int) -> int | None:
    """The memory an Excel workbook needs to be cut, when it is more than the worker has: the
    same check as converting it (B2-01). ``None``: it fits, or another format."""
    if format_id is not FormatId.XLSX:
        return None
    needed = limits.estimated_memory(FormatId.XLSX, size)
    return needed if needed > limits.worker_memory else None


def page_ranges(pages: int, cut: Cut, size: int) -> tuple[tuple[int, int], ...]:
    """The parts' first and last pages (1-based, inclusive). Into N parts: as even as possible,
    the first ones a page longer; never more parts than pages, never an empty one."""
    if pages <= 0:
        return ()
    if cut is Cut.PAGES:
        return tuple((first, min(first + size - 1, pages)) for first in range(1, pages + 1, size))
    count = min(size, pages)
    base, extra = divmod(pages, count)
    ranges = []
    first = 1
    for index in range(count):
        length = base + (1 if index < extra else 0)
        ranges.append((first, first + length - 1))
        first += length
    return tuple(ranges)


def word_ranges(
    words: tuple[int, ...], size: int
) -> tuple[tuple[tuple[int, int], ...], tuple[int, ...]]:
    """Whole pages, in order, up to ``size`` words a part (feature 024); a page larger than
    ``size`` is a part alone. The ranges, and which parts are over the size."""
    ranges: list[tuple[int, int]] = []
    over: list[int] = []
    total = 0
    for page, count in enumerate(words, start=1):
        if ranges and total + count <= size:
            ranges[-1] = (ranges[-1][0], page)
            total += count
        else:
            ranges.append((page, page))
            total = count
        if total > size and len(ranges) not in over:
            over.append(len(ranges))
    return tuple(ranges), tuple(over)


def _pdf(
    item: PlannedConversion,
    spec: SplitSpec,
    runner: ConversionRunner,
    cutter: PageCutter,
    cancel: CancelToken,
    where: list[str],
    stage: PartStage,
) -> tuple[int, tuple[ConversionNote, ...]]:
    over: tuple[int, ...] = ()
    if spec.cut is Cut.WORDS:
        words = cutter.page_words(item, cancel)
        if not any(words):  # scanned: never one silent part (ADR-0045)
            raise ConversionError(ErrorCode.NOTHING_TO_MEASURE, f"{len(words)} pages, no text")
        ranges, over = word_ranges(words, spec.size)
    else:
        ranges = page_ranges(cutter.count_pages(item, cancel), spec.cut, spec.size)
    if not ranges:
        raise ConversionError(ErrorCode.CORRUPT_FILE, "the PDF has no pages")
    notes: list[tuple[int, ConversionNote]] = []
    for index, (first, last) in enumerate(ranges, start=1):
        name = part_name(spec, item.target.name, index, len(ranges))
        where[0] = f"part {index} of {len(ranges)} (pages {first}-{last}): "
        pdf = stage.at(item.target / f"{name}.pdf")
        atomic_write_bytes(pdf, cutter.cut(item, first, last, cancel), inside=item.output_root)
        if spec.keep.markdown:
            part = replace(
                item, source=pdf, target=stage.at(item.target / f"{name}.md"), split=None
            )
            result = runner.convert(part, cancel)
            atomic_write(part.target, result.markdown, inside=item.output_root)
            notes.extend((first, note) for note in result.notes)
            if not spec.keep.original:
                remove_regular_file(pdf, inside=item.output_root)
    return len(ranges), merged(notes) + over_size(over)


def _markdown(
    item: PlannedConversion,
    spec: SplitSpec,
    cutter: PageCutter,
    cancel: CancelToken,
    stage: PartStage,
) -> tuple[int, tuple[ConversionNote, ...]]:
    """A Markdown file's parts, cut at its headings in the worker; always Markdown (024)."""
    parts, over = cutter.markdown_parts(item, spec.cut.value, spec.size, cancel)
    if not any(part.strip() for part in parts):  # nothing in it
        raise ConversionError(ErrorCode.EMPTY_FILE, "an empty Markdown file")
    for index, text in enumerate(parts, start=1):
        name = part_name(spec, item.target.name, index, len(parts))
        text = relinked(text, item.source.parent, item.target)  # its images still show
        atomic_write(stage.at(item.target / f"{name}.md"), text, inside=item.output_root)
    return len(parts), over_size(over)


def split_one(
    item: PlannedConversion, runner: ConversionRunner, cutter: PageCutter, cancel: CancelToken
) -> ConversionOutcome:
    """Cut ``item.source`` and write its parts into ``item.target``; ``Cancelled`` propagates.
    The earlier parts are replaced only when every new one is written (``PartStage``)."""
    spec = item.split
    assert spec is not None
    where = [""]
    stage = PartStage(item, spec)
    try:
        if item.detection.format is FormatId.MARKDOWN:
            count, notes = _markdown(item, spec, cutter, cancel, stage)
        elif item.detection.format in OWN_FORMAT_PARTS:  # text, CSV, Excel (feature 027)
            count, notes = split_file(item, spec, runner, cutter, cancel, stage)
        else:
            count, notes = _pdf(item, spec, runner, cutter, cancel, where, stage)
        stage.commit()
        if spec.cut is Cut.PARTS and count < spec.size:  # said, never a silent "done" (B1-02)
            item_note = NoteItem(f"{spec.size} → {count}")
            notes = (*notes, ConversionNote(NoteKind.PARTS_FEWER, (item_note,)))
    except ConversionError as error:
        status = OutcomeStatus.STOPPED if error.code in STOPPING_CODES else OutcomeStatus.FAILED
        return ConversionOutcome(
            item, status, error.code, where[0] + error.detail, limit=error.limit
        )
    except OSError as error:
        detail = f"{where[0]}{type(error).__name__}: {error}"
        return ConversionOutcome(item, OutcomeStatus.FAILED, ErrorCode.WRITE_FAILED, detail)
    finally:
        stage.discard()  # nothing left after a commit; otherwise the new parts go
    return ConversionOutcome(item, OutcomeStatus.CONVERTED, notes=notes, parts=count)
