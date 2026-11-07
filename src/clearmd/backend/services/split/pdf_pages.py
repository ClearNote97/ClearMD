"""A PDF's pages counted and copied into a new PDF, whole and in order (feature 023, ADR-0044).

PDFium copies the pages with everything they use (fonts, images); nothing inside them is changed.
It runs in the worker process, as every reading of a document does (ADR-0015)."""

import io
from pathlib import Path

import pypdfium2 as pdfium

from clearmd.backend.schemas.errors import ConversionError, ErrorCode

# PDFium's load errors (fpdfview.h): 2 file, 3 format, 4 password, 5 security handler.
_BROKEN = {2, 3}
_LOCKED = {4, 5}


def _open(path: Path) -> pdfium.PdfDocument:
    try:
        data = path.read_bytes()
    except OSError as error:
        detail = f"{type(error).__name__}: {error}"
        raise ConversionError(ErrorCode.SOURCE_UNREADABLE, detail) from None
    try:
        return pdfium.PdfDocument(data)
    except pdfium.PdfiumError as error:
        code = getattr(error, "err_code", None)
        detail = f"PDFium could not open it: {error}"
        if code in _LOCKED:
            raise ConversionError(ErrorCode.PASSWORD_PROTECTED, detail) from None
        if code in _BROKEN:
            raise ConversionError(ErrorCode.CORRUPT_FILE, detail) from None
        raise ConversionError(ErrorCode.CONVERSION_FAILED, detail) from None


def count_pages(path: Path) -> int:
    document = _open(path)
    try:
        return len(document)
    finally:
        document.close()


def cut_pages(path: Path, first: int, last: int) -> bytes:
    """A new PDF with the pages ``first``..``last`` (1-based, inclusive) of ``path``."""
    source = _open(path)
    try:
        if not 1 <= first <= last <= len(source):
            raise ConversionError(
                ErrorCode.CONVERSION_FAILED, f"pages {first}-{last} of {len(source)}"
            )
        part = pdfium.PdfDocument.new()
        try:
            part.import_pages(source, list(range(first - 1, last)))
            stream = io.BytesIO()
            part.save(stream)
            return stream.getvalue()
        finally:
            part.close()
    finally:
        source.close()
