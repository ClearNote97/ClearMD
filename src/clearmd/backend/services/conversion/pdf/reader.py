"""PDFium reads the text: the whole document, page by page, as lines (feature 008, ADR-0030).

Two passes: the fonts' codes first (a moved font is known only from all its text), then the
lines, one page's characters at a time. The pieces are in ``pdfium`` (every call into PDFium),
``lines`` (characters to lines) and ``blocks`` (tables and equations in a page).
"""

import pypdfium2.raw as raw

from clearmd.backend.services.conversion.images import ImageSink
from clearmd.backend.services.conversion.pdf.decode import shift
from clearmd.backend.services.conversion.pdf.lines.paging import build_page
from clearmd.backend.services.conversion.pdf.model import Document, Page
from clearmd.backend.services.conversion.pdf.pdfium.crop import pictured
from clearmd.backend.services.conversion.pdf.pdfium.document import text_pages
from clearmd.backend.services.conversion.pdf.pdfium.fonts import MAX_PAGE_CHARS, Fonts, count
from clearmd.backend.services.conversion.pdf.pdfium.page_chars import page_chars, tight_boxes
from clearmd.backend.services.conversion.pdf.pdfium.page_objects import page_rules
from clearmd.backend.services.conversion.pdf.pdfium.pictures import pictures, placed

MAX_CROPS = 500  # equations cropped in a document: past it, the others are written as text


MAX_DOCUMENT_PIXELS = 400_000_000  # all of a document's pictures (a logo on every page counts)


def read(document: object, images: ImageSink | None = None) -> Document:
    """Two passes: the fonts' codes first (a moved font is known only from all its text), then
    the lines, page by page: only one page's characters are ever held (code review of 008)."""
    fonts = Fonts()
    for textpage, _height, _page_handle in text_pages(document):
        if textpage is not None:
            count(textpage, fonts)
    shifts = [shift(codes) if fonts.unmapped(n) else 0 for n, codes in enumerate(fonts.codes)]
    unmapped = [fonts.unmapped(n) for n in range(len(fonts.codes))]
    result = Document([], decoded_fonts=sum(1 for distance in shifts if distance))
    # The pixels pictures and equations may take in the whole document, and the equations cropped.
    budget = [MAX_DOCUMENT_PIXELS, MAX_CROPS]
    for textpage, height, handle in text_pages(document):
        if textpage is not None and raw.FPDFText_CountChars(textpage) > MAX_PAGE_CHARS:
            result.cut_pages += 1
        chars = None if textpage is None else page_chars(textpage, fonts)
        while len(shifts) < len(fonts.codes):  # a font first met in the second pass: as read
            shifts.append(0)
            unmapped.append(False)
        rules, bars = page_rules(handle) if handle is not None and chars is not None else ([], [])
        page = (
            Page()
            if chars is None
            else build_page(chars, shifts, unmapped, result, rules, bars, tight_boxes(textpage))
        )
        if images is not None and handle is not None:
            page.lines = [pictured(handle, line, images, budget) for line in page.lines]
            page.lines = placed(page.lines, pictures(document, handle, images, budget))
        page.height = height
        result.pages.append(page)
    return result
