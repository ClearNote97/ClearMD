"""Split one file into parts of whole pages (feature 023, ADR-0044).

The pages are counted and copied in the worker. Here: the cut, the parts' names, and writing
them. A part's Markdown is converted part by part, each within the time limit (ADR-0015).
Overwriting replaces only the parts of an earlier cut; other files in the folder stay.
"""

import os
import re
from dataclasses import replace
from pathlib import Path

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.formats import FormatId, Strategy
from clearmd.backend.schemas.limits import Limits
from clearmd.backend.schemas.models import ConversionOutcome, OutcomeStatus, PlannedConversion
from clearmd.backend.schemas.notes import ConversionNote, NoteItem, NoteKind
from clearmd.backend.schemas.split import Cut, SplitSpec
from clearmd.backend.use_cases.cancel import CancelToken
from clearmd.backend.use_cases.output_files import (
    atomic_write,
    atomic_write_bytes,
    remove_regular_file,
)
from clearmd.backend.use_cases.ports import ConversionRunner, PageCutter

STOPPING_CODES = frozenset({ErrorCode.TIMED_OUT, ErrorCode.OUT_OF_MEMORY})


def split_cost(limits: Limits, size: int, split: SplitSpec) -> float:
    """Copying pages is quick; converting the parts costs what converting the PDF does."""
    copy = limits.estimated_seconds(FormatId.PDF, size, Strategy.FULL) / 20
    if split.keep.markdown:
        return copy + limits.estimated_seconds(FormatId.PDF, size, Strategy.FULL)
    return copy


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


def part_name(spec: SplitSpec, name: str, index: int, total: int) -> str:
    """A part's name without extension; the index padded to the total's width (sorts right)."""
    width = len(str(total))
    return spec.part_name.format(name=name, index=str(index).zfill(width), total=total)


def _earlier_part(spec: SplitSpec, name: str) -> re.Pattern[str]:
    """Any part of an earlier cut of ``name``: ClearMD's own names only."""
    pattern = re.escape(spec.part_name)
    for field, value in (("name", re.escape(name)), ("index", r"\d+"), ("total", r"\d+")):
        pattern = pattern.replace(re.escape("{" + field + "}"), value)
    return re.compile(pattern + r"\.(?:pdf|md)")


def _remove_earlier_parts(item: PlannedConversion, spec: SplitSpec) -> None:
    folder = item.target
    if not os.path.isdir(folder) or os.path.islink(folder):
        return
    own = _earlier_part(spec, item.target.name)
    with os.scandir(folder) as entries:
        old = [Path(entry.path) for entry in entries if own.fullmatch(entry.name)]
    for path in old:
        remove_regular_file(path, inside=item.output_root)


def _shifted(pages: str, shift: int) -> str:
    """``"1–3"`` of a part that starts at the PDF's page 11: ``"11–13"``."""
    return re.sub(r"\d+", lambda number: str(int(number[0]) + shift), pages)


def _merged(notes: list[tuple[int, ConversionNote]]) -> tuple[ConversionNote, ...]:
    """The parts' notes as one file's: a note per kind, and pages counted in the whole PDF (a
    part's page 1 is the PDF's page ``first``)."""
    items: dict[NoteKind, list[NoteItem]] = {}
    for first, note in notes:
        shift = first - 1
        found = items.setdefault(note.kind, [])
        for item in note.items:
            if note.kind is NoteKind.PDF_PAGES_WITHOUT_TEXT:
                item = NoteItem(_shifted(item.subject, shift))
            if item not in found:
                found.append(item)
    return tuple(ConversionNote(kind, tuple(found)) for kind, found in items.items())


def split_one(
    item: PlannedConversion, runner: ConversionRunner, cutter: PageCutter, cancel: CancelToken
) -> ConversionOutcome:
    """Cut ``item.source`` and write its parts into ``item.target``; ``Cancelled`` propagates."""
    spec = item.split
    assert spec is not None
    current = ""
    try:
        ranges = page_ranges(cutter.count_pages(item, cancel), spec.cut, spec.size)
        if not ranges:
            raise ConversionError(ErrorCode.CORRUPT_FILE, "the PDF has no pages")
        _remove_earlier_parts(item, spec)
        notes: list[tuple[int, ConversionNote]] = []
        for index, (first, last) in enumerate(ranges, start=1):
            name = part_name(spec, item.target.name, index, len(ranges))
            current = f"part {index} of {len(ranges)} (pages {first}-{last}): "
            pdf = item.target / f"{name}.pdf"
            atomic_write_bytes(pdf, cutter.cut(item, first, last, cancel), inside=item.output_root)
            if spec.keep.markdown:
                part = replace(item, source=pdf, target=item.target / f"{name}.md", split=None)
                result = runner.convert(part, cancel)
                atomic_write(part.target, result.markdown, inside=item.output_root)
                notes.extend((first, note) for note in result.notes)
                if not spec.keep.original:
                    remove_regular_file(pdf, inside=item.output_root)
    except ConversionError as error:
        status = OutcomeStatus.STOPPED if error.code in STOPPING_CODES else OutcomeStatus.FAILED
        detail = current + error.detail
        return ConversionOutcome(item, status, error.code, detail, limit=error.limit)
    except OSError as error:
        detail = f"{current}{type(error).__name__}: {error}"
        return ConversionOutcome(item, OutcomeStatus.FAILED, ErrorCode.WRITE_FAILED, detail)
    return ConversionOutcome(item, OutcomeStatus.CONVERTED, notes=_merged(notes), parts=len(ranges))
