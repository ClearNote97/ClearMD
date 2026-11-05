"""ClearMD's own PDF converter (feature 008, ADR-0030): PDFium reads, ClearMD cleans.

Only text is converted: a scanned page (an image) has none, and ClearMD does no OCR; the
summary tells which pages. Worker process only, like every converter (ADR-0015).
"""

from pathlib import Path

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.schemas.limits import Limits
from clearmd.backend.schemas.models import ConversionResult, Detection
from clearmd.backend.schemas.notes import ConversionNote, NoteItem, NoteKind
from clearmd.backend.services.conversion.images import ImageSink
from clearmd.backend.services.conversion.pdf.cleaner import clean
from clearmd.backend.services.conversion.pdf.pdfium.document import opened
from clearmd.backend.services.conversion.pdf.reader import read
from clearmd.backend.services.conversion.safe_files import read_regular_file

MAX_LISTED_PAGES = 1000  # as many items as any note lists (ADR-0023); ranges count as one
MAX_BYTES = Limits().max_file_size  # read once, at most this: the file may grow after planning


def page_ranges(numbers: list[int]) -> tuple[NoteItem, ...]:
    """1, 2, 3, 7 → "1–3", "7": a million blank pages are one item, not a million."""
    items: list[NoteItem] = []
    start = previous = None
    for number in [*numbers, None]:
        if number is not None and previous is not None and number == previous + 1:
            previous = number
            continue
        if start is not None:
            items.append(NoteItem(str(start) if start == previous else f"{start}–{previous}"))
        start = previous = number
    return tuple(items[:MAX_LISTED_PAGES])


class PdfConverter:
    def convert(
        self,
        source: Path,
        detection: Detection,
        target: Path,
        *,
        images: ImageSink | None = None,
    ) -> ConversionResult:
        try:
            data = read_regular_file(source, MAX_BYTES)
        except OSError as error:
            raise ConversionError(ErrorCode.SOURCE_UNREADABLE, str(error)) from error
        with opened(data) as pdf:
            document = read(pdf, images)
        del data
        cleaned = clean(document)
        notes: list[ConversionNote] = []
        if cleaned.empty_pages:
            items = page_ranges(cleaned.empty_pages)
            notes.append(ConversionNote(NoteKind.PDF_PAGES_WITHOUT_TEXT, items))
        if document.decoded_fonts:
            notes.append(ConversionNote(NoteKind.PDF_TEXT_DECODED))
        if document.unreadable:
            notes.append(ConversionNote(NoteKind.PDF_TEXT_UNREADABLE))
        if document.cut_pages:
            notes.append(ConversionNote(NoteKind.PAGE_CUT))
        if cleaned.running_removed:
            notes.append(ConversionNote(NoteKind.PDF_RUNNING_REMOVED))
        return ConversionResult(cleaned.markdown, tuple(notes))
