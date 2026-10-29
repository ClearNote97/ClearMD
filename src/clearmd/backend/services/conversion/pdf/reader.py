"""PDFium reads the text: lines with their size, weight and place (feature 008, ADR-0030).

PDFium keeps the spaces that pdfminer loses in many papers ("interactionsbasedonvalues"), and
reads rotated text the right way round. A font without a usable character map gives its glyph
codes instead of letters ("(6&8(/$" for "ESCUELA"): when PDFium says a font has no map, and its
codes are letters moved by one distance, with the space moved to a control character, the font is
read back (``_shift``). What still cannot be read is shown as "�" and counted.

PDFium's own C API is called (pypdfium2's raw bindings): ClearMD opens the document itself, so a
load error is read when it happens, and a PDF without pages is an empty document.
"""

import ctypes
import math
from array import array
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field

import pypdfium2.raw as raw

from clearmd.backend.schemas.errors import ConversionError, ErrorCode

_LINE_END = 0x0A
_SKIPPED = {0x0D, 0xFEFF}
_SOFT_HYPHENS = {0x02, 0xAD, 0xFFFE}  # what PDFium gives for a hyphen that breaks a word
SOFT_HYPHEN = "­"
UNREADABLE = "�"
_BOLD_WEIGHT = 600
_BOLD_NAMES = ("bold", "black", "heavy", "semibold", "demi")
_FORCE_BOLD = 1 << 18  # the font descriptor's ForceBold flag
MIN_SHIFT_SHARE = 0.03  # a font whose text holds this share of control characters is suspect
MIN_LETTER_SHARE = 0.75  # and is read back only if its moved codes are then mostly letters
VOWELS = frozenset("aeiouáéíóúAEIOUÁÉÍÓÚ")
# A TrueType font embedded without a character map often numbers its glyphs in the Macintosh
# standard order (Apple's "post" table): glyph 3 is the space, 36 is "A", so code + 29 is the
# letter, and glyphs 98-198 are these. Past 198 a font's own order differs: unreadable.
MAC_ORDER_SHIFT = 29
_MAC_ORDER = (
    "ÄÅÇÉÑÖÜáàâäãåçéèêëíìîïñóòôöõúùûü†°¢£§•¶ß®©™´¨≠ÆØ∞±≤≥¥µ∂∑∏π∫ªºΩæø¿¡¬√ƒ≈∆«»… "
    "ÀÃÕŒœ–—“”‘’÷◊ÿŸ⁄¤‹›ﬁﬂ‡·‚„‰"
)
_MAC_FIRST = 98

# PDFium's load errors (fpdfview.h), by name.
_PASSWORD = {raw.FPDF_ERR_PASSWORD}
_BROKEN = {raw.FPDF_ERR_FILE, raw.FPDF_ERR_FORMAT, raw.FPDF_ERR_SECURITY}  # 5: a handler it lacks


@dataclass
class Line:
    text: str
    size: float  # the height of the text, in points: headings are taller
    bold: bool
    top: float  # page coordinates (origin at the bottom): a larger gap starts a paragraph
    bottom: float


LETTER_HEIGHT = 792.0  # points: a page whose height PDFium cannot give


@dataclass
class Page:
    lines: list[Line] = field(default_factory=list)
    height: float = LETTER_HEIGHT


@dataclass
class Document:
    pages: list[Page]
    decoded_fonts: int = 0  # fonts read back from moved codes (the summary tells it)
    unreadable: int = 0  # characters that could not be read (shown as "�")


class _Chars:
    """One page's characters, compact: a few bytes each, not a Python object each (a book of
    millions of characters must fit in the worker's memory, code review of 008)."""

    def __init__(self) -> None:
        self.codes = array("I")
        self.fonts = array("I")  # the font's number in the document (``_Fonts``)
        self.sizes = array("f")
        self.bottoms = array("f")
        self.tops = array("f")
        self.bold = array("B")


class _Fonts:
    """A number per font of the document, by its name, flags and whether PDFium has a map for
    it (the same in both passes, whatever PDFium does with its objects; two fonts both called
    "Helvetica", one without a map, stay two); its codes, and whether that map is missing."""

    def __init__(self) -> None:
        self.number: dict[tuple[bytes, int, bool], int] = {}
        self.codes: list[Counter[int]] = []
        self.unmapped: list[bool] = []
        self.bold: list[bool] = []

    def at(self, textpage: object, index: int) -> int:
        name = ctypes.create_string_buffer(128)
        flags = ctypes.c_int()
        raw.FPDFText_GetFontInfo(textpage, index, name, len(name), ctypes.byref(flags))
        unmapped = raw.FPDFText_HasUnicodeMapError(textpage, index) == 1
        key = (name.value, flags.value, unmapped)
        if key not in self.number:
            self.number[key] = len(self.codes)
            self.codes.append(Counter())
            self.unmapped.append(unmapped)
            # By the weight the font declares, or else by its name ("Helvetica-Bold",
            # "Arial,Bold"): the standard fonts and many embedded ones declare no weight.
            lowered = name.value.decode("latin-1").lower()
            self.bold.append(
                raw.FPDFText_GetFontWeight(textpage, index) >= _BOLD_WEIGHT
                or bool(flags.value & _FORCE_BOLD)
                or any(word in lowered for word in _BOLD_NAMES)
            )
        return self.number[key]


def _finite(value: float) -> float:
    return value if math.isfinite(value) else 0.0


def _each_font(textpage: object, fonts: _Fonts) -> Iterator[tuple[int, int]]:
    """(index, font) of every character of the page; the font is looked up once per text
    object, not per character."""
    last_object: int | None = None
    font = 0
    for index in range(max(raw.FPDFText_CountChars(textpage), 0)):
        handle = raw.FPDFText_GetTextObject(textpage, index)
        address = ctypes.cast(handle, ctypes.c_void_p).value or 0
        if address != last_object:
            last_object = address
            font = fonts.at(textpage, index)
        yield index, font


def _count(textpage: object, fonts: _Fonts) -> None:
    """The first pass: each font's codes."""
    for index, font in _each_font(textpage, fonts):
        fonts.codes[font][raw.FPDFText_GetUnicode(textpage, index)] += 1


def _page_chars(textpage: object, fonts: _Fonts) -> _Chars:
    """The second pass, one page at a time: its characters, compact."""
    chars = _Chars()
    rect = raw.FS_RECTF()
    for index, font in _each_font(textpage, fonts):
        raw.FPDFText_GetLooseCharBox(textpage, index, ctypes.byref(rect))
        bottom, top = _finite(rect.bottom), _finite(rect.top)
        code = raw.FPDFText_GetUnicode(textpage, index)
        chars.codes.append(min(code, 0x10FFFF + 1))  # past Unicode: unreadable
        chars.fonts.append(font)
        chars.sizes.append(max(top - bottom, 0.0))
        chars.bottoms.append(bottom)
        chars.tops.append(top)
        chars.bold.append(fonts.bold[font])
    return chars


def _shift(codes: Counter[int]) -> int:
    """How far one font's codes are moved from the letters they draw (0: not moved). The space is
    the commonest character of any text: moved to a control character, it gives the distance;
    the rest must then be mostly letters, with vowels among them, as words are."""
    total = sum(codes.values())
    controls = {code: n for code, n in codes.items() if code < 0x20 and code not in (9, 10, 13)}
    if not controls or sum(controls.values()) < MIN_SHIFT_SHARE * total:
        return 0
    space = max(controls, key=controls.__getitem__)
    distance = 0x20 - space
    rest = {code: n for code, n in codes.items() if code != space and code not in _SKIPPED}
    moved = {chr(_decoded(code, distance)): n for code, n in rest.items() if code < 0x110000}
    letters = sum(n for char, n in moved.items() if char.isalpha())
    vowels = sum(n for char, n in moved.items() if char in VOWELS)
    others = sum(rest.values()) or 1
    return distance if letters >= MIN_LETTER_SHARE * others and vowels >= 0.2 * letters else 0


def _decoded(code: int, distance: int) -> int:
    if not distance:
        return code
    if distance == MAC_ORDER_SHIFT and code >= _MAC_FIRST:
        index = code - _MAC_FIRST
        return ord(_MAC_ORDER[index]) if index < len(_MAC_ORDER) else 0xFFFD
    moved = code + distance
    return moved if moved < 0x80 else 0xFFFD


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


def _text_pages(document: object) -> Iterator[tuple[object | None, float]]:
    """Each page's text page (None: a page PDFium could not load) and height, closed after."""
    for index in range(max(raw.FPDF_GetPageCount(document), 0)):
        page = raw.FPDF_LoadPage(document, index)
        if not page:
            yield None, LETTER_HEIGHT
            continue
        try:
            height = _finite(raw.FPDF_GetPageHeightF(page))
            textpage = raw.FPDFText_LoadPage(page)
            try:
                yield (textpage or None), (height if height > 0 else LETTER_HEIGHT)
            finally:
                if textpage:
                    raw.FPDFText_ClosePage(textpage)
        finally:
            raw.FPDF_ClosePage(page)


def read(document: object) -> Document:
    """Two passes: the fonts' codes first (a moved font is known only from all its text), then
    the lines, page by page: only one page's characters are ever held (code review of 008)."""
    fonts = _Fonts()
    for textpage, _height in _text_pages(document):
        if textpage is not None:
            _count(textpage, fonts)
    shifts = [
        _shift(codes) if unmapped else 0
        for codes, unmapped in zip(fonts.codes, fonts.unmapped, strict=True)
    ]
    result = Document([], decoded_fonts=sum(1 for distance in shifts if distance))
    for textpage, height in _text_pages(document):
        page = (
            Page()
            if textpage is None
            else _page(_page_chars(textpage, fonts), shifts, fonts, result)
        )
        page.height = height
        result.pages.append(page)
    return result


def _page(chars: _Chars, shifts: list[int], fonts: _Fonts, document: Document) -> Page:
    page = Page()
    start = 0
    for index in range(len(chars.codes) + 1):
        if index == len(chars.codes) or chars.codes[index] == _LINE_END:
            if index > start:
                line = _line(chars, range(start, index), shifts, fonts, document)
                if line.text.strip():
                    page.lines.append(line)
            start = index + 1
    return page


def _line(chars: _Chars, span: range, shifts: list[int], fonts: _Fonts, document: Document) -> Line:
    text: list[str] = []
    high = 0  # PDFium gives a character past U+FFFF as two halves (a surrogate pair)
    visible: list[int] = []
    for index in span:
        font = chars.fonts[index]
        raw_code = chars.codes[index]
        if raw_code in _SKIPPED:
            continue
        code = _decoded(raw_code, shifts[font])
        if 0xD800 <= code < 0xDC00:
            high = code
            continue
        if 0xDC00 <= code < 0xE000:
            if high:
                text.append(chr(0x10000 + ((high - 0xD800) << 10) + (code - 0xDC00)))
            high = 0
            continue
        high = 0
        if code in _SOFT_HYPHENS:
            text.append(SOFT_HYPHEN)
        elif code == 0x09 or code == 0x20:
            text.append(" ")
            continue
        elif code < 0x20 or code == 0x7F or code > 0x10FFFF or code == 0xFFFD:
            # A code no map turned into a character: never dropped silently (ADR-0022).
            document.unreadable += 1
            text.append(UNREADABLE)
        elif fonts.unmapped[font] and not shifts[font]:
            document.unreadable += 1  # a font without a map, not read back: its letters are wrong
            text.append(chr(code))
        else:
            text.append(chr(code))
        visible.append(index)
    shown = visible or list(span)
    sizes = Counter(round(chars.sizes[index], 1) for index in shown)
    return Line(
        " ".join("".join(text).split()),
        sizes.most_common(1)[0][0],
        sum(chars.bold[index] for index in shown) * 2 > len(shown),
        max(chars.tops[index] for index in shown),
        min(chars.bottoms[index] for index in shown),
    )
