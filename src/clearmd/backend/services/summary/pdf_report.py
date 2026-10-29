"""Write Resumen_ClearMD.pdf: the summary in the app's look (ADR-0031, ADR-0027).

The same ``SummaryContent`` as the Markdown, drawn with PDFium (bundled for reading PDFs,
ADR-0030) in Helvetica, one of the PDF standard fonts every reader has: nothing is embedded, so
the report weighs a few KB. Real, selectable text, a teal band, the marks as coloured circles, the
converted files as a table. No link, no action, no JavaScript: only text and shapes.

The standard fonts hold the Windows Latin characters (all of English and Spanish); a character
outside them, in a name from the user's files, is drawn as "?" (the Markdown keeps it). Names are
drawn as plain text, control characters shown escaped.
"""

import ctypes
import io
from collections.abc import Iterator
from dataclasses import dataclass
from functools import cache

import pypdfium2 as pdfium
import pypdfium2.raw as raw

from clearmd.backend.schemas.formats import PDF_SUMMARY_NAME
from clearmd.backend.schemas.models import OutputRootReport
from clearmd.backend.schemas.notes import ConversionNote
from clearmd.backend.services.summary.content import (
    MARKDOWN_FOLDER,
    Entry,
    Mark,
    SummaryBuilder,
    SummaryContent,
)
from clearmd.backend.use_cases.output_files import atomic_write_bytes
from clearmd.i18n import Catalog, printable

REGULAR, BOLD = b"Helvetica", b"Helvetica-Bold"
SPACE_EM = 0.278  # Helvetica's space, in ems (its metrics: Adobe's AFM)
WIDTH, HEIGHT = 595.0, 842.0  # A4, in points
MARGIN = 48.0
BAND = 76.0  # the teal band at the top of the first page
NOTE_ITEMS = 20
TABLE_SHARES = (0.26, 0.15, 0.26, 0.23, 0.10)  # document, folder, result, format, time

Colour = tuple[int, int, int]


def _rgb(value: str) -> Colour:
    return int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16)


# The app's light palette (ADR-0027): a printed page is light.
TEXT, MUTED, BORDER = _rgb("#1B2733"), _rgb("#5B6672"), _rgb("#DCE2E7")
ACCENT, SHAPE, WHITE = _rgb("#0F766E"), _rgb("#D7EEEA"), _rgb("#FFFFFF")
MARK_COLOURS: dict[Mark, Colour] = {
    Mark.DONE: _rgb("#15803D"),
    Mark.ATTENTION: _rgb("#B45309"),
    Mark.FAILED: _rgb("#B91C1C"),
    Mark.STOPPED: _rgb("#5B6672"),
}
LEFT_OUT = _rgb("#A9B4BE")  # a file that was not tried: a quiet grey dot


@dataclass(frozen=True)
class _Run:
    text: str
    bold: bool = False
    colour: Colour = TEXT


class _Canvas:
    """Pages of text and shapes, top to bottom; a new page when one is full."""

    def __init__(self, footer: str) -> None:
        self.pdf = pdfium.PdfDocument.new()
        self._footer = _latin(footer)
        self.fonts = {
            False: raw.FPDFText_LoadStandardFont(self.pdf.raw, REGULAR),
            True: raw.FPDFText_LoadStandardFont(self.pdf.raw, BOLD),
        }
        self.page: pdfium.PdfPage | None = None
        self.y = 0.0
        self.pages = 0

    def new_page(self) -> None:
        self.finish_page()
        self.page = self.pdf.new_page(WIDTH, HEIGHT)
        self.pages += 1
        self.y = HEIGHT - MARGIN

    def finish_page(self) -> None:
        if self.page is not None:
            footer = f"{self._footer} · {self.pages}"
            self.text(MARGIN, MARGIN / 2, footer, 8, _Run(footer, False, MUTED))
            raw.FPDFPage_GenerateContent(self.page.raw)
            self.page = None

    def room(self, height: float) -> None:
        """A new page when ``height`` does not fit above the bottom margin."""
        if self.page is None or self.y - height < MARGIN:
            self.new_page()

    def text(self, x: float, y: float, text: str, size: float, run: _Run) -> None:
        assert self.page is not None
        obj = _text_object(self.pdf.raw, self.fonts[run.bold], text, size)
        raw.FPDFPageObj_SetFillColor(obj, *run.colour, 255)
        raw.FPDFPageObj_Transform(obj, 1, 0, 0, 1, x, y)
        raw.FPDFPage_InsertObject(self.page.raw, obj)

    def rect(self, x: float, y: float, w: float, h: float, colour: Colour) -> None:
        assert self.page is not None
        obj = raw.FPDFPageObj_CreateNewRect(x, y, w, h)
        raw.FPDFPageObj_SetFillColor(obj, *colour, 255)
        raw.FPDFPath_SetDrawMode(obj, raw.FPDF_FILLMODE_WINDING, False)
        raw.FPDFPage_InsertObject(self.page.raw, obj)

    def circle(self, cx: float, cy: float, r: float, colour: Colour) -> None:
        """Four Bézier arcs (k: the standard circle constant)."""
        assert self.page is not None
        k = 0.5523 * r
        obj = raw.FPDFPageObj_CreateNewPath(cx + r, cy)
        raw.FPDFPath_BezierTo(obj, cx + r, cy + k, cx + k, cy + r, cx, cy + r)
        raw.FPDFPath_BezierTo(obj, cx - k, cy + r, cx - r, cy + k, cx - r, cy)
        raw.FPDFPath_BezierTo(obj, cx - r, cy - k, cx - k, cy - r, cx, cy - r)
        raw.FPDFPath_BezierTo(obj, cx + k, cy - r, cx + r, cy - k, cx + r, cy)
        raw.FPDFPath_Close(obj)
        raw.FPDFPageObj_SetFillColor(obj, *colour, 255)
        raw.FPDFPath_SetDrawMode(obj, raw.FPDF_FILLMODE_WINDING, False)
        raw.FPDFPage_InsertObject(self.page.raw, obj)

    def save(self) -> bytes:
        self.finish_page()
        out = io.BytesIO()
        self.pdf.save(out)
        self.pdf.close()
        return out.getvalue()


def _text_object(document: object, font: object, text: str, size: float) -> object:
    obj = raw.FPDFPageObj_CreateTextObj(document, font, size)
    encoded = (text + "\0").encode("utf-16-le")
    buffer = ctypes.create_string_buffer(encoded, len(encoded))
    raw.FPDFText_SetText(obj, ctypes.cast(buffer, ctypes.POINTER(raw.FPDF_WCHAR)))
    return obj


class _Measure:
    """Text widths in the standard fonts, from PDFium itself (a word's box, at 1000 pt)."""

    def __init__(self) -> None:
        self._pdf = pdfium.PdfDocument.new()
        self._fonts = {
            False: raw.FPDFText_LoadStandardFont(self._pdf.raw, REGULAR),
            True: raw.FPDFText_LoadStandardFont(self._pdf.raw, BOLD),
        }

    @cache  # noqa: B019 -- one measurer for the process, the words of every report
    def word(self, word: str, bold: bool) -> float:
        if not word:
            return 0.0
        obj = _text_object(self._pdf.raw, self._fonts[bold], word, 1000)
        left, bottom, right, top = (ctypes.c_float() for _ in range(4))
        raw.FPDFPageObj_GetBounds(
            obj, *(ctypes.byref(value) for value in (left, bottom, right, top))
        )
        raw.FPDFPageObj_Destroy(obj)
        return (right.value - left.value) / 1000


@cache
def _measure() -> _Measure:
    return _Measure()


def _width(text: str, size: float, bold: bool) -> float:
    """Words measured, spaces counted: a word's box leaves out the space around it."""
    words = text.split(" ")
    spaces = len(words) - 1
    return size * (sum(_measure().word(word, bold) for word in words) + spaces * SPACE_EM)


def _latin(text: str) -> str:
    """What the standard fonts can draw: Windows Latin; any other character is "?"."""
    return text.encode("cp1252", errors="replace").decode("cp1252")


def _shown(text: str) -> str:
    """Text from the user's files, drawn as it may be printed."""
    return " ".join(printable(text).split())


def _runs(runs: list[_Run]) -> list[_Run]:
    return [_Run(_latin(run.text), run.bold, run.colour) for run in runs]


def _wrap(runs: list[_Run], size: float, width: float) -> Iterator[list[_Run]]:
    """Words of several runs into lines no wider than ``width`` (a word too long is cut)."""
    line: list[_Run] = []
    used = 0.0
    for run in _runs(runs):
        for index, word in enumerate(run.text.split(" ")):
            piece = word if index == 0 else " " + word
            piece_width = _width(piece, size, run.bold)
            if line and used + piece_width > width:
                yield line
                line, used = [], 0.0
                piece = piece.lstrip()
                piece_width = _width(piece, size, run.bold)
            while piece and piece_width > width:  # one word wider than the line
                cut = len(piece)
                while cut > 1 and _width(piece[:cut], size, run.bold) > width:
                    cut -= 1
                yield [*line, _Run(piece[:cut], run.bold, run.colour)]
                line, used = [], 0.0
                piece = piece[cut:]
                piece_width = _width(piece, size, run.bold)
            if piece:
                line.append(_Run(piece, run.bold, run.colour))
                used += piece_width
    if line:
        yield line


def _fit(text: str, size: float, width: float, bold: bool = False) -> str:
    """One cell's text, cut with "…" when it does not fit."""
    if _width(text, size, bold) <= width:
        return text
    while text and _width(text + "…", size, bold) > width:
        text = text[:-1]
    return text + "…"


class PdfReport:
    def __init__(self, catalog: Catalog, *, version: str) -> None:
        self._catalog = catalog
        self._builder = SummaryBuilder(catalog, version=version)

    def write(self, report: OutputRootReport) -> None:
        data = self.render(self._builder.build(report))
        atomic_write_bytes(report.root / PDF_SUMMARY_NAME, data, inside=report.root)

    def render(self, content: SummaryContent) -> bytes:
        canvas = _Canvas(self._catalog.text("summary.title"))
        canvas.new_page()
        self._band(canvas, content)
        self._headline(canvas, content)
        text = self._catalog.text
        self._heading(canvas, text("summary.where_title"))
        self._paragraph(canvas, [_Run(text("summary.where", folder=f"{MARKDOWN_FOLDER}/"))])
        if content.attention:
            self._heading(canvas, text("summary.attention"))
            for entry in content.attention:
                self._entry(canvas, entry)
        if content.converted:
            self._heading(canvas, text("summary.converted"))
            self._table(canvas, content)
        for key, entries in (
            ("summary.left_out", content.left_out),
            ("summary.kept", content.kept),
            ("summary.cancelled", content.cancelled),
        ):
            if entries:
                self._heading(canvas, text(key))
                for entry in entries:
                    self._entry(canvas, entry)
        return canvas.save()

    # --- Pieces ------------------------------------------------------------------------------

    def _band(self, canvas: _Canvas, content: SummaryContent) -> None:
        canvas.rect(0, HEIGHT - BAND, WIDTH, BAND, ACCENT)
        title = self._catalog.text("summary.title")
        canvas.text(MARGIN, HEIGHT - 44, _latin(title), 20, _Run(title, True, WHITE))
        line = _latin(content.batch_line)
        canvas.text(MARGIN, HEIGHT - 62, line, 9, _Run(line, False, SHAPE))
        canvas.y = HEIGHT - BAND - 28

    def _headline(self, canvas: _Canvas, content: SummaryContent) -> None:
        runs = [_Run(content.headline, True)]
        if content.attention_line:
            runs.append(_Run(" " + content.attention_line, False, MUTED))
        lines = list(_wrap(runs, 14, WIDTH - 2 * MARGIN - 24))
        canvas.room(20 * len(lines))
        canvas.circle(MARGIN + 7, canvas.y + 4, 7, MARK_COLOURS[content.mark])
        for line in lines:
            self._line(canvas, MARGIN + 24, line, 14)
            canvas.y -= 20
        canvas.y -= 6

    def _heading(self, canvas: _Canvas, text: str) -> None:
        canvas.room(44)
        canvas.y -= 16
        canvas.text(MARGIN, canvas.y, _latin(text), 12, _Run(text, True, ACCENT))
        canvas.rect(MARGIN, canvas.y - 6, WIDTH - 2 * MARGIN, 0.8, BORDER)
        canvas.y -= 22

    def _paragraph(
        self, canvas: _Canvas, runs: list[_Run], *, indent: float = 0, size: float = 10
    ) -> None:
        for line in _wrap(runs, size, WIDTH - 2 * MARGIN - indent):
            canvas.room(size + 4)
            self._line(canvas, MARGIN + indent, line, size)
            canvas.y -= size + 4

    def _line(self, canvas: _Canvas, x: float, runs: list[_Run], size: float) -> None:
        for run in runs:
            canvas.text(x, canvas.y, run.text, size, run)
            x += _width(run.text, size, run.bold)

    def _entry(self, canvas: _Canvas, entry: Entry) -> None:
        canvas.room(18)
        colour = MARK_COLOURS[entry.mark] if entry.mark else LEFT_OUT
        canvas.circle(MARGIN + 4, canvas.y + 3.5, 3.5, colour)
        runs = [_Run(_shown(entry.name), True)]
        if entry.folder:
            folder = self._catalog.text("summary.in_folder", folder=_shown(entry.folder))
            runs.append(_Run(" " + folder, False, MUTED))
        if entry.result:
            runs.append(_Run(f" » {_shown(entry.result)}", False, MUTED))  # no "→" in Latin
        if entry.message:
            runs.append(_Run(f" — {entry.message}"))
        self._paragraph(canvas, runs, indent=14)
        for note in entry.notes:
            self._paragraph(canvas, [_Run(f"· {self.describe(note)}")], indent=26, size=9)
        if entry.detail:
            detail = f"{self._catalog.text('summary.technical_detail')}: {entry.detail}"
            self._paragraph(canvas, [_Run(_shown(detail), False, MUTED)], indent=26, size=8)
        canvas.y -= 4

    def describe(self, note: ConversionNote) -> str:
        shown = []
        for item in note.items[:NOTE_ITEMS]:
            subject = _shown(item.subject)
            reason = item.reason and self._catalog.text(f"note.reason.{item.reason}")
            shown.append(f"{subject} ({reason})" if reason else subject)
        listed = ", ".join(shown)
        if len(note.items) > NOTE_ITEMS:
            listed += self._catalog.text("note.and_more", count=len(note.items) - NOTE_ITEMS)
        return self._catalog.text(note.kind.key, items=listed)

    def _table(self, canvas: _Canvas, content: SummaryContent) -> None:
        text = self._catalog.text
        full = WIDTH - 2 * MARGIN
        widths = [share * full for share in TABLE_SHARES]
        header = [
            text("summary.col_document"),
            text("summary.col_folder"),
            text("summary.col_result"),
            text("summary.col_format"),
            text("summary.col_time"),
        ]

        def row(cells: list[str], *, bold: bool, ground: Colour | None) -> None:
            canvas.room(18)
            if ground is not None:
                canvas.rect(MARGIN, canvas.y - 5, full, 17, ground)
            x = MARGIN
            for cell, width in zip(cells, widths, strict=True):
                shown = _fit(_latin(cell), 9, width - 8, bold)
                canvas.text(x + 4, canvas.y, shown, 9, _Run(shown, bold))
                x += width
            canvas.y -= 17

        row(header, bold=True, ground=SHAPE)
        for converted in content.converted:
            cells = [
                _shown(converted.name),
                _shown(converted.folder) or "—",
                _shown(converted.result),
                converted.format,
                converted.time,
            ]
            row(cells, bold=False, ground=None)
            canvas.rect(MARGIN, canvas.y + 12, full, 0.5, BORDER)
