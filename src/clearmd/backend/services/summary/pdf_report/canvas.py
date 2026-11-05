"""``Canvas``: pages of text and shapes, top to bottom, drawn with PDFium."""

import io

import pypdfium2 as pdfium
import pypdfium2.raw as raw

from clearmd.backend.services.summary.pdf_report.metrics import text_object
from clearmd.backend.services.summary.pdf_report.text import latin
from clearmd.backend.services.summary.pdf_report.theme import (
    BOLD,
    HEIGHT,
    MARGIN,
    MUTED,
    REGULAR,
    WIDTH,
    Colour,
    Run,
)


class Canvas:
    """Pages of text and shapes, top to bottom; a new page when one is full."""

    def __init__(self, footer: str) -> None:
        self.pdf = pdfium.PdfDocument.new()
        self._footer = latin(footer)
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
            self.text(MARGIN, MARGIN / 2, footer, 8, Run(footer, False, MUTED))
            raw.FPDFPage_GenerateContent(self.page.raw)
            self.page = None

    def room(self, height: float) -> None:
        """A new page when ``height`` does not fit above the bottom margin."""
        if self.page is None or self.y - height < MARGIN:
            self.new_page()

    def text(self, x: float, y: float, text: str, size: float, run: Run) -> None:
        assert self.page is not None
        obj = text_object(self.pdf.raw, self.fonts[run.bold], text, size)
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
