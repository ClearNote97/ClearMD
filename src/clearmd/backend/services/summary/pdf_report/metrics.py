"""Text widths by PDFium: ink of a text object, Latin advances, and how much text fits.

Helvetica's metrics are measured once per font and kept for the process (``advances_of`` is the
only cache).
"""

import ctypes
from functools import cache

import pypdfium2 as pdfium
import pypdfium2.raw as raw

from clearmd.backend.services.summary.pdf_report.theme import BOLD, REGULAR


def text_object(document: object, font: object, text: str, size: float) -> object:
    """A PDFium text object holding ``text``."""
    obj = raw.FPDFPageObj_CreateTextObj(document, font, size)
    encoded = (text + "\0").encode("utf-16-le")
    buffer = ctypes.create_string_buffer(encoded, len(encoded))
    raw.FPDFText_SetText(obj, ctypes.cast(buffer, ctypes.POINTER(raw.FPDF_WCHAR)))
    return obj


def ink(document: object, font: object, text: str) -> float:
    """The width of ``text``'s ink at 1000 pt, by PDFium."""
    obj = text_object(document, font, text, 1000)
    left, bottom, right, top = (ctypes.c_float() for _ in range(4))
    raw.FPDFPageObj_GetBounds(obj, *(ctypes.byref(value) for value in (left, bottom, right, top)))
    raw.FPDFPageObj_Destroy(obj)
    return right.value - left.value


@cache
def advances_of(bold: bool) -> dict[str, float]:
    """Each Windows Latin character's advance in ems, measured once: the ink of "H?H" less the
    ink of "HH" is the advance of "?", whatever its own ink (code review of 009: a word's ink
    is narrower than the room it takes). At most 256 entries per font, kept for the process."""
    pdf = pdfium.PdfDocument.new()
    try:
        font = raw.FPDFText_LoadStandardFont(pdf.raw, BOLD if bold else REGULAR)
        base = ink(pdf.raw, font, "HH")
        table = {}
        for code in range(0x20, 0x100):
            char = bytes([code]).decode("cp1252", errors="replace")
            if char != "�":
                table[char] = (ink(pdf.raw, font, f"H{char}H") - base) / 1000
        return table
    finally:
        pdf.close()


def width(text: str, size: float, bold: bool) -> float:
    """How wide ``text`` is drawn at ``size``."""
    advances = advances_of(bold)
    return size * sum(advances.get(char, 0.556) for char in text)


def cut(text: str, size: float, width: float, bold: bool) -> int:
    """How many characters of ``text`` fit in ``width``: one pass, never a search."""
    advances = advances_of(bold)
    used = 0.0
    for index, char in enumerate(text):
        used += size * advances.get(char, 0.556)
        if used > width:
            return max(index, 1)
    return len(text)
