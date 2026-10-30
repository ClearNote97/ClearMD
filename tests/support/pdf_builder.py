"""Small PDFs written by hand for the PDF converter's tests (feature 008): pages of text at given
places, sizes and weights; a font without a character map; rotated or sideways text; a page with
no text."""

from collections.abc import Sequence
from dataclasses import dataclass

# The Macintosh standard glyph order from 98 on, as ClearMD's reader decodes it (ADR-0030).
_MAC_ORDER = "ÄÅÇÉÑÖÜáàâäãåçéèêëíìîïñóòôöõúùûü"
GLYPH_CODE = "\ue001"  # in a "glyphs" text: the next character is written as its raw code


@dataclass(frozen=True)
class Text:
    text: str
    y: float  # the baseline, from the bottom of a letter page (792 points)
    size: float = 11
    font: str = "regular"  # "regular", "bold", or "glyphs": codes, no character map
    x: float = 72
    rotated: bool = False  # upside down (180°)
    sideways: bool = False  # turned a quarter, to read upwards (a table set sideways, 013)
    downwards: bool = False  # turned a quarter the other way, to read downwards


@dataclass(frozen=True)
class Box:
    """A filled box: a thin one is a rule (a ruled table's cell side, 013)."""

    x: float
    y: float
    width: float
    height: float


_FONTS = {"regular": "F1", "bold": "F2", "glyphs": "F3"}


def _escape(data: bytes) -> bytes:
    return data.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def _codes(text: str, font: str) -> bytes:
    if font != "glyphs":
        return text.encode("cp1252")
    out = bytearray()
    raw_next = False
    for char in text:
        if char == GLYPH_CODE:
            raw_next = True
        elif raw_next:
            out.append(ord(char))  # a glyph past the standard order (Í is 204 in Arial's own)
            raw_next = False
        elif char in _MAC_ORDER:
            out.append(98 + _MAC_ORDER.index(char))
        elif " " <= char <= "~":
            out.append(ord(char) - 29)  # glyph 3 is the space, glyph 36 is "A"
        else:
            raise ValueError(f"no glyph code for {char!r}: write it with GLYPH_CODE")
    return bytes(out)


def _stream(texts: Sequence[Text | Box]) -> bytes:
    out = bytearray()
    for item in texts:
        if isinstance(item, Box):
            out += b"%g %g %g %g re f\n" % (item.x, item.y, item.width, item.height)
            continue
        matrix = (
            b"-1 0 0 -1" if item.rotated
            else b"0 1 -1 0" if item.sideways
            else b"0 -1 1 0" if item.downwards
            else b"1 0 0 1"
        )  # fmt: skip
        out += b"BT /%s %g Tf %s %g %g Tm (" % (
            _FONTS[item.font].encode(),
            item.size,
            matrix,
            item.x,
            item.y,
        )
        out += _escape(_codes(item.text, item.font)) + b") Tj ET\n"
    return bytes(out)


def build_pdf(pages: Sequence[Sequence[Text | Box]]) -> bytes:
    """A PDF with one page per list (an empty list: a page with no text, like a scan)."""
    glyph_codes = sorted(set(range(1, 256)))
    differences = " ".join(f"{code} /g{code}" for code in glyph_codes)
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"",  # the page tree, once the pages are numbered
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding << /Type /Encoding "
        + f"/Differences [{differences}] >> >>".encode(),
    ]
    kids = []
    for texts in pages:
        stream = _stream(texts)
        objects.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
        content = len(objects)
        objects.append(
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font "
            b"<< /F1 3 0 R /F2 4 0 R /F3 5 0 R >> >> /Contents %d 0 R >>" % content
        )
        kids.append(len(objects))
    refs = " ".join(f"{kid} 0 R" for kid in kids)
    objects[1] = f"<< /Type /Pages /Kids [{refs}] /Count {len(kids)} >>".encode()
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(out)


def paragraph(lines: list[str], *, top: float, size: float = 11, leading: float = 14) -> list[Text]:
    """Lines one under another, as a paragraph of body text."""
    return [Text(line, top - index * leading, size) for index, line in enumerate(lines)]
