"""Opening a PDF with PDFium's C API and walking its pages (feature 008, ADR-0030)."""

import ctypes
import math
from collections.abc import Iterator
from contextlib import contextmanager

import pypdfium2.raw as raw

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.services.conversion.pdf.model import LETTER_HEIGHT

# PDFium's load errors (fpdfview.h), by name.
# A security handler PDFium does not have (5) is encryption it cannot open: locked, not broken.
_PASSWORD = {raw.FPDF_ERR_PASSWORD, raw.FPDF_ERR_SECURITY}
_BROKEN = {raw.FPDF_ERR_FILE, raw.FPDF_ERR_FORMAT}


def finite(value: float) -> float:
    return value if math.isfinite(value) else 0.0


@contextmanager
def opened(data: bytes) -> Iterator[object]:
    """PDFium's document for ``data``, closed afterwards. The buffer lives as long as it."""
    buffer = ctypes.create_string_buffer(data, len(data))
    handle = raw.FPDF_LoadMemDocument64(buffer, len(data), None)
    if not handle:
        error = raw.FPDF_GetLastError()
        detail = f"PDFium could not open it (error {error})"
        if error in _PASSWORD:
            raise ConversionError(ErrorCode.PASSWORD_PROTECTED, detail)
        if error in _BROKEN:
            raise ConversionError(ErrorCode.CORRUPT_FILE, detail)
        raise ConversionError(ErrorCode.CONVERSION_FAILED, detail)
    try:
        yield handle
    finally:
        raw.FPDF_CloseDocument(handle)
        del buffer


def text_pages(document: object) -> Iterator[tuple[object | None, float, object | None]]:
    """Each page's text page (None: a page PDFium could not load), height and page, closed
    after."""
    for index in range(max(raw.FPDF_GetPageCount(document), 0)):
        page = raw.FPDF_LoadPage(document, index)
        if not page:
            yield None, LETTER_HEIGHT, None
            continue
        try:
            height = finite(raw.FPDF_GetPageHeightF(page))
            textpage = raw.FPDFText_LoadPage(page)
            try:
                yield (textpage or None), (height if height > 0 else LETTER_HEIGHT), page
            finally:
                if textpage:
                    raw.FPDFText_ClosePage(textpage)
        finally:
            raw.FPDF_ClosePage(page)
