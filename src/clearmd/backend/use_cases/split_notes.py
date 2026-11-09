"""The notes of a split file (features 023, 024): its parts' notes as one file's, and the parts
larger than the size."""

import re

from clearmd.backend.schemas.errors import ConversionError
from clearmd.backend.schemas.models import ConversionResult, PlannedConversion
from clearmd.backend.schemas.notes import ConversionNote, NoteItem, NoteKind
from clearmd.backend.use_cases.cancel import CancelToken
from clearmd.backend.use_cases.ports import ConversionRunner


def _shifted(pages: str, shift: int) -> str:
    """``"1–3"`` of a part that starts at the PDF's page 11: ``"11–13"``."""
    return re.sub(r"\d+", lambda number: str(int(number[0]) + shift), pages)


def merged(notes: list[tuple[int, ConversionNote]]) -> tuple[ConversionNote, ...]:
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


def over_size(parts: tuple[int, ...]) -> tuple[ConversionNote, ...]:
    """Parts larger than the size: a page or a paragraph that cannot be cut (feature 024)."""
    if not parts:
        return ()
    return (ConversionNote(NoteKind.PARTS_OVER_SIZE, tuple(NoteItem(str(n)) for n in parts)),)


def part_markdown(
    runner: ConversionRunner, part: PlannedConversion, cancel: CancelToken
) -> ConversionResult | None:
    """A part's Markdown; ``None`` when that part could not be converted (stopped, failed). The
    parts already cut stay: one part that stops never costs the others (audit v3, B1-02)."""
    try:
        return runner.convert(part, cancel)
    except ConversionError:
        return None


def not_converted(parts: list[int]) -> tuple[ConversionNote, ...]:
    """Parts whose Markdown could not be made: their original part stays in the folder."""
    if not parts:
        return ()
    return (ConversionNote(NoteKind.PARTS_NOT_CONVERTED, tuple(NoteItem(str(n)) for n in parts)),)
