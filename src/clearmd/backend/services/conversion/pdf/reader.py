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
import io
import math
from array import array
from collections import Counter
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field

import pypdfium2 as pdfium
import pypdfium2.raw as raw
from PIL import Image

from clearmd.backend.schemas.errors import ConversionError, ErrorCode
from clearmd.backend.services.conversion.images import ImageSink
from clearmd.backend.services.conversion.pdf.equations import Placed, find_equations
from clearmd.backend.services.conversion.pdf.latex import Bar, Glyph, to_latex
from clearmd.backend.services.conversion.pdf.lattice import Rule, find_lattices, rule
from clearmd.backend.services.conversion.pdf.tables import Table, Word, find_tables

_LINE_END = 0x0A
# The letters Unicode has as scripts: a script made only of them is written with them (014).
_SUPERSCRIPTS = dict(
    zip(
        "0123456789+-−=()abcdefghijklmnoprstuvwxyzABDEGHIJKLMNOPRTUVW′″θ*",
        "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁻⁼⁽⁾ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖʳˢᵗᵘᵛʷˣʸᶻᴬᴮᴰᴱᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾᴿᵀᵁⱽᵂ′″ᶿ*",
        strict=True,
    )
)
_SUBSCRIPTS = dict(
    zip("0123456789+-−=()aehijklmnoprstuvx", "₀₁₂₃₄₅₆₇₈₉₊₋₋₌₍₎ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ", strict=True)
)
_SKIPPED = {0x0D, 0xFEFF}
_SOFT_HYPHENS = {0x02, 0xAD, 0xFFFE}  # what PDFium gives for a hyphen that breaks a word
SOFT_HYPHEN = "­"
UNREADABLE = "�"
_BOLD_NAMES = ("bold", "black", "heavy", "semibold", "demi")
_FORCE_BOLD = 1 << 18  # the font descriptor's ForceBold flag
TURN_RADIANS = 0.01  # a character turned less than this from a quarter turn is on it
UPRIGHT, CLOCKWISE, COUNTERCLOCKWISE, ASLANT = range(4)  # how a character is turned
LOOK_AHEAD = 4  # characters looked at past a line's end (its carriage return, a space)
ROW_OVERLAP = 0.5  # of the shorter box: two characters this much level are on one row
SCRIPT_GAP_EMS = 0.5  # a script starts at most this far from what it is set on
SCRIPT_SIZE = 0.85  # a character this much smaller than its line's text may be a script
RAISED_EMS = 0.12  # its baseline this far above the line's (in its size) is a superscript
LOWERED_EMS = 0.08  # this far below, a subscript
HUG_EMS = 0.12  # a space narrower than this (a word's is about a quarter) touches a script
BASE_SHARE = 0.15  # a character within this share of the text's size is text
TEXT_SHARE = 0.2  # of a line's characters: a size this many share may be the text's
DELIMITER_RATIO = 1.6  # larger than the commonest size: a tall brace or bracket
NEW_ROW_SHARE = 0.5  # of a sideways letter's height: a character this far across is on another row
ROW_SLACK = 1.0  # points: a line within a table's top and bottom is one of its rows
ROW_SHARE = 0.35  # of a letter's height: pieces this close vertically are on one row
COLUMN_SHARE = 0.5  # of a letter's height: an equation's columns, about a letter wide
MAX_COLUMN = 200  # an equation's piece starts at most this far right
CROP_SCALE = 2.0  # an equation's picture: 144 dots per inch
CROP_PAD = 3.0  # points around it
MAX_CROPS = 500  # equations cropped in a document: past it, the others are written as text
MAX_PAGE_POINTS = 14_400.0  # PDF's largest page side (200 inches)
INK_LEVEL = 160  # a grey this dark is ink
APART_PIXELS = 6  # a blank this tall (at 144 dpi) parts the equation from a neighbour's sliver
TRIM_MARGIN = 6  # pixels of white kept around the ink
MAX_PAGE_CHARS = 200_000  # a dense page of a book holds ~5,000; past this, the rest is left out
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
# A security handler PDFium does not have (5) is encryption it cannot open: locked, not broken.
_PASSWORD = {raw.FPDF_ERR_PASSWORD, raw.FPDF_ERR_SECURITY}
_BROKEN = {raw.FPDF_ERR_FILE, raw.FPDF_ERR_FORMAT}


@dataclass
class Line:
    text: str
    size: float  # the height of the text, in points: headings are taller
    bold: bool
    top: float  # page coordinates (origin at the bottom): a larger gap starts a paragraph
    bottom: float
    image: str = ""  # a picture's link in the images folder: the line is the picture (012)
    turn: int = UPRIGHT  # a line of a table set sideways is turned (013)
    equation: tuple[str, ...] = ()  # the line is a display equation, its rows as laid out (013)
    left: float = 0.0
    right: float = 0.0
    table: tuple[tuple[str, ...], ...] = ()  # the line is a table found on the page (013)
    span: tuple[int, int] = (0, 0)  # its characters on the page (start, stop)
    latex: str = ""  # an equation rebuilt as LaTeX from its pieces (015)


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
    cut_pages: int = 0  # pages with more characters than any page holds: their first part kept


class _Chars:
    """One page's characters, compact: a few bytes each, not a Python object each (a book of
    millions of characters must fit in the worker's memory, code review of 008)."""

    def __init__(self) -> None:
        self.codes = array("I")
        self.fonts = array("I")  # the font's number in the document (``_Fonts``)
        self.sizes = array("f")
        self.bottoms = array("f")
        self.tops = array("f")
        self.lefts = array("f")
        self.rights = array("f")
        self.turns = array("B")  # upright, a quarter turn either way, or aslant
        self.font_sizes = array("f")  # the font's size, as set: a script's is smaller (014)
        self.baselines = array("f")  # where it stands: a script's is raised or lowered
        self.bold = array("B")


class _Fonts:
    """A number per font of the document: PDFium keeps each font once per open document, so its
    address (with its name and flags) names it in both passes, and two fonts that share a name
    stay two (adversarial check of 008). Its codes; how many PDFium could not map; its weight."""

    def __init__(self) -> None:
        self.number: dict[tuple[int, bytes, int], int] = {}
        self.codes: list[Counter[int]] = []
        self.errors: list[int] = []  # characters PDFium found no map for
        self.bold: list[bool] = []

    def at(self, textpage: object, index: int, address: int) -> int:
        name = ctypes.create_string_buffer(128)
        flags = ctypes.c_int()
        raw.FPDFText_GetFontInfo(textpage, index, name, len(name), ctypes.byref(flags))
        key = (address, name.value, flags.value)
        if key not in self.number:
            self.number[key] = len(self.codes)
            self.codes.append(Counter())
            self.errors.append(0)
            # By its name ("Helvetica-Bold", "Arial,Bold") or the ForceBold flag only: a font
            # that declares no weight gets one from its stems, and plain Arial reads 695.
            lowered = name.value.decode("latin-1").lower()
            self.bold.append(
                bool(flags.value & _FORCE_BOLD) or any(word in lowered for word in _BOLD_NAMES)
            )
        return self.number[key]

    def unmapped(self, font: int) -> bool:
        """Most of its characters had no map (one mapped space first proves nothing)."""
        return self.errors[font] * 2 >= max(sum(self.codes[font].values()), 1)


def _finite(value: float) -> float:
    return value if math.isfinite(value) else 0.0


def _each_font(textpage: object, fonts: _Fonts) -> Iterator[tuple[int, int]]:
    """(index, font) of every character of the page; the font is looked up once per text
    object, not per character."""
    last_object: int | None = None
    font = 0
    for index in range(min(max(raw.FPDFText_CountChars(textpage), 0), MAX_PAGE_CHARS)):
        handle = raw.FPDFText_GetTextObject(textpage, index)
        address = ctypes.cast(handle, ctypes.c_void_p).value or 0
        if address != last_object:
            last_object = address
            pointer = raw.FPDFTextObj_GetFont(handle) if handle else None
            font_address = (ctypes.cast(pointer, ctypes.c_void_p).value or 0) if pointer else 0
            font = fonts.at(textpage, index, font_address)
        yield index, font


def _count(textpage: object, fonts: _Fonts) -> None:
    """The first pass: each font's codes."""
    for index, font in _each_font(textpage, fonts):
        fonts.codes[font][raw.FPDFText_GetUnicode(textpage, index)] += 1
        if raw.FPDFText_HasUnicodeMapError(textpage, index) == 1:
            fonts.errors[font] += 1


def _page_chars(textpage: object, fonts: _Fonts) -> _Chars:
    """The second pass, one page at a time: its characters, compact."""
    chars = _Chars()
    rect = raw.FS_RECTF()
    box, unicode, angle = (
        raw.FPDFText_GetLooseCharBox,
        raw.FPDFText_GetUnicode,
        raw.FPDFText_GetCharAngle,
    )
    pointer = ctypes.byref(rect)
    font_size, origin, placed = (
        raw.FPDFText_GetFontSize,
        raw.FPDFText_GetCharOrigin,
        raw.FPDFText_GetMatrix,
    )
    matrix = raw.FS_MATRIX()
    matrix_pointer = ctypes.byref(matrix)
    x, y = ctypes.c_double(), ctypes.c_double()
    origin_x, origin_y = ctypes.byref(x), ctypes.byref(y)
    # The same font with the same box height is the same size, its baseline the same height above
    # its box: PDFium is asked again only when either changes (review of 014: the two calls per
    # character cost a quarter of the reading).
    measured: tuple[int, float, float, float] | None = None  # font, height, size, baseline lift
    for index, font in _each_font(textpage, fonts):
        box(textpage, index, pointer)
        bottom, top = _finite(rect.bottom), _finite(rect.top)
        code = unicode(textpage, index)
        chars.codes.append(min(code, 0x10FFFF + 1))  # past Unicode: unreadable
        chars.fonts.append(font)
        chars.sizes.append(max(top - bottom, 0.0))
        chars.bottoms.append(bottom)
        chars.tops.append(top)
        chars.lefts.append(_finite(rect.left))
        chars.rights.append(_finite(rect.right))
        turned = angle(textpage, index)
        upright = turned == 0.0
        chars.turns.append(UPRIGHT if upright else _turn(turned))  # nearly all: upright
        height = top - bottom
        if upright and measured is not None and measured[:2] == (font, height):
            chars.font_sizes.append(measured[2])
            chars.baselines.append(bottom + measured[3])
        else:
            # The size as drawn: the font's size scaled by its matrix ("1 Tf" and a 9.46 matrix);
            # its height, the matrix's y column ("50 Tz" or "3 0 0 1 cm" scale the width alone).
            scale = (
                math.hypot(matrix.c, matrix.d) if placed(textpage, index, matrix_pointer) else 1.0
            )
            size = _finite(font_size(textpage, index) * scale)
            baseline = _finite(y.value) if origin(textpage, index, origin_x, origin_y) else bottom
            chars.font_sizes.append(size)
            chars.baselines.append(baseline)
            if upright and code > 0x20:
                measured = (font, height, size, baseline - bottom)
        chars.bold.append(fonts.bold[font])
    return chars


def _turn(angle: float) -> int:
    """How a character is turned, from PDFium's angle (radians, 0 to 2π, measured clockwise: a
    table set sideways to read upwards is at 3π/2)."""
    for target, turn in ((0, UPRIGHT), (2 * math.pi, UPRIGHT), (0.5 * math.pi, CLOCKWISE)):
        if abs(angle - target) < TURN_RADIANS:
            return turn
    return COUNTERCLOCKWISE if abs(angle - 1.5 * math.pi) < TURN_RADIANS else ASLANT


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


def _text_pages(document: object) -> Iterator[tuple[object | None, float, object | None]]:
    """Each page's text page (None: a page PDFium could not load), height and page, closed
    after."""
    for index in range(max(raw.FPDF_GetPageCount(document), 0)):
        page = raw.FPDF_LoadPage(document, index)
        if not page:
            yield None, LETTER_HEIGHT, None
            continue
        try:
            height = _finite(raw.FPDF_GetPageHeightF(page))
            textpage = raw.FPDFText_LoadPage(page)
            try:
                yield (textpage or None), (height if height > 0 else LETTER_HEIGHT), page
            finally:
                if textpage:
                    raw.FPDFText_ClosePage(textpage)
        finally:
            raw.FPDF_ClosePage(page)


MIN_PICTURE_POINTS = 24.0  # smaller: a bullet, a rule, a logo's speck
MAX_PICTURE_PIXELS = 40_000_000  # a picture's own pixels, read before it is decoded
MAX_DOCUMENT_PIXELS = 400_000_000  # all of a document's pictures (a logo on every page counts)
BAR_THICKNESS = 1.5  # points: a fraction's bar is a thin line
MIN_BAR = 2.0  # points: shorter is a dot
MAX_BAR = 400.0  # points: longer is a rule across the page
MAX_BARS = 2000  # a page's bars looked at
MAX_PAGE_OBJECTS = 100_000  # a page's objects looked at for pictures, forms' included
MAX_FORM_DEPTH = 4  # forms inside forms


def _pictures(document: object, page: object, sink: ImageSink, budget: list[int]) -> list[Line]:
    """The page's pictures as lines at their place, each kept by the sink (012). Each is decoded
    at its own size, checked before (never rendered at the size it is drawn: a 2 x 2 picture
    drawn 12,000 points wide, review of 012), within the document's budget of pixels; those
    inside a form object are found too, placed where the form stands."""
    lines: list[Line] = []
    for obj, box in _image_objects(page):
        data = _picture_png(obj, budget)
        link = sink.add(data) if data is not None else None
        if data is None:
            sink.left_out += 1
        if link is not None:
            lines.append(Line("", 0.0, False, box[3], box[1], image=link))
    return lines


def _rules(page: object) -> tuple[list[Rule], list[Bar]]:
    """The page's thin paths: the rules a ruled table is drawn with (013), and the short level
    ones an equation draws (its fractions' bars, 015)."""
    found: list[Rule] = []
    bars: list[Bar] = []
    left, bottom, right, top = (ctypes.c_float() for _ in range(4))
    for index in range(min(max(raw.FPDFPage_CountObjects(page), 0), MAX_PAGE_OBJECTS)):
        obj = raw.FPDFPage_GetObject(page, index)
        if not obj or raw.FPDFPageObj_GetType(obj) != raw.FPDF_PAGEOBJ_PATH:
            continue
        raw.FPDFPageObj_GetBounds(obj, *(ctypes.byref(v) for v in (left, bottom, right, top)))
        box = [_finite(v.value) for v in (left, bottom, right, top)]
        found_rule = rule(*box)
        if found_rule is not None:
            found.append(found_rule)
        if box[3] - box[1] <= BAR_THICKNESS and MIN_BAR <= box[2] - box[0] <= MAX_BAR:
            bars.append(Bar(box[0], box[2], (box[1] + box[3]) / 2))
    return found, bars[:MAX_BARS]


def _image_objects(page: object) -> Iterator[tuple[object, list[float]]]:
    """The page's image objects with their place: (left, bottom, right, top)."""
    left, bottom, right, top = (ctypes.c_float() for _ in range(4))
    visited = 0
    pending: list[tuple[object, int, list[float] | None]] = [(page, 0, None)]
    while pending:
        holder, depth, place = pending.pop(0)
        in_form = holder is not page
        count = (
            raw.FPDFFormObj_CountObjects(holder) if in_form else raw.FPDFPage_CountObjects(holder)
        )
        for index in range(max(count, 0)):
            visited += 1
            if visited > MAX_PAGE_OBJECTS:
                return
            obj = (
                raw.FPDFFormObj_GetObject(holder, index)
                if in_form
                else raw.FPDFPage_GetObject(holder, index)
            )
            if not obj:
                continue
            kind = raw.FPDFPageObj_GetType(obj)
            if kind not in (raw.FPDF_PAGEOBJ_IMAGE, raw.FPDF_PAGEOBJ_FORM):
                continue
            box = place
            if box is None:
                raw.FPDFPageObj_GetBounds(
                    obj, *(ctypes.byref(v) for v in (left, bottom, right, top))
                )
                box = [_finite(v.value) for v in (left, bottom, right, top)]
            if kind == raw.FPDF_PAGEOBJ_FORM:
                if depth < MAX_FORM_DEPTH:
                    pending.append((obj, depth + 1, box))
            elif box[2] - box[0] >= MIN_PICTURE_POINTS and box[3] - box[1] >= MIN_PICTURE_POINTS:
                yield obj, box


def _picture_png(obj: object, budget: list[int]) -> bytes | None:
    """The picture at its own size, as PNG; None when it is too large or cannot be decoded."""
    width, height = ctypes.c_uint(), ctypes.c_uint()
    if not raw.FPDFImageObj_GetImagePixelSize(obj, ctypes.byref(width), ctypes.byref(height)):
        return None
    pixels = width.value * height.value
    if not 0 < pixels <= MAX_PICTURE_PIXELS or pixels > budget[0]:
        return None
    budget[0] -= pixels
    bitmap = raw.FPDFImageObj_GetBitmap(obj)
    if not bitmap:
        return None
    picture = pdfium.PdfBitmap.from_raw(bitmap)
    picture.warn_on_close = False  # closed only once the PNG is written from a copy of it
    try:
        data = io.BytesIO()
        picture.to_pil().convert("RGB").save(data, "PNG")
        return data.getvalue()
    except (ValueError, OSError, MemoryError):
        return None
    finally:
        picture.close()


def _pictured(page: object, line: Line, images: ImageSink, budget: list[int]) -> Line:
    """An equation, as it looks on the page, when the images folder is on (013): within the
    document's pixels and crops (each renders the page; review of 013), else its text."""
    if not line.equation or line.latex or budget[1] <= 0:
        return line
    budget[1] -= 1
    data = _cropped(page, line, budget)
    link = images.add(data) if data is not None else None
    if link is None:
        return line
    return Line("", line.size, False, line.top, line.bottom, image=link, left=line.left)


def _placed(lines: list[Line], pictures: list[Line]) -> list[Line]:
    """Each picture before the first line below its top: the reading order of the page."""
    for picture in sorted(pictures, key=lambda line: -line.top):
        at = next((i for i, line in enumerate(lines) if line.top < picture.top), len(lines))
        lines.insert(at, picture)
    return lines


def read(document: object, images: ImageSink | None = None) -> Document:
    """Two passes: the fonts' codes first (a moved font is known only from all its text), then
    the lines, page by page: only one page's characters are ever held (code review of 008)."""
    fonts = _Fonts()
    for textpage, _height, _page_handle in _text_pages(document):
        if textpage is not None:
            _count(textpage, fonts)
    shifts = [_shift(codes) if fonts.unmapped(n) else 0 for n, codes in enumerate(fonts.codes)]
    unmapped = [fonts.unmapped(n) for n in range(len(fonts.codes))]
    result = Document([], decoded_fonts=sum(1 for distance in shifts if distance))
    # The pixels pictures and equations may take in the whole document, and the equations cropped.
    budget = [MAX_DOCUMENT_PIXELS, MAX_CROPS]
    for textpage, height, handle in _text_pages(document):
        if textpage is not None and raw.FPDFText_CountChars(textpage) > MAX_PAGE_CHARS:
            result.cut_pages += 1
        chars = None if textpage is None else _page_chars(textpage, fonts)
        while len(shifts) < len(fonts.codes):  # a font first met in the second pass: as read
            shifts.append(0)
            unmapped.append(False)
        rules, bars = _rules(handle) if handle is not None and chars is not None else ([], [])
        page = (
            Page()
            if chars is None
            else _page(chars, shifts, unmapped, result, rules, bars, _tight_boxes(textpage))
        )
        if images is not None and handle is not None:
            page.lines = [_pictured(handle, line, images, budget) for line in page.lines]
            page.lines = _placed(page.lines, _pictures(document, handle, images, budget))
        page.height = height
        result.pages.append(page)
    return result


def _page(
    chars: _Chars,
    shifts: list[int],
    unmapped: list[bool],
    document: Document,
    rules: list[Rule] | None = None,
    bars: list[Bar] | None = None,
    tight: "_Boxes | None" = None,
) -> Page:
    page = Page()
    words: dict[int, list[Word]] = {UPRIGHT: [], CLOCKWISE: [], COUNTERCLOCKWISE: []}
    start = 0
    last = -1  # the last character drawn (with a width): where a sideways row goes on from
    extent = [math.inf, -math.inf]  # the line's bottom and top so far
    for index in range(len(chars.codes) + 1):
        ended = index == len(chars.codes) or (
            chars.codes[index] == _LINE_END and not _goes_on(chars, last, index, extent)
        )
        if not ended and last >= start and _new_row(chars, last, index):
            ended = True  # PDFium runs a sideways table's rows into one line: one per row
            next_start = index
        else:
            next_start = index + 1
        if ended:
            if index > start:
                line = _line(chars, range(start, index), shifts, unmapped, document, words)
                if line.text.strip():
                    page.lines.append(line)
            start = next_start
            extent[:] = [math.inf, -math.inf]
        if (
            index < len(chars.codes)
            and chars.codes[index] > 0x20  # a space PDFium adds is drawn nowhere in particular
            and chars.rights[index] > chars.lefts[index]
        ):
            last = index
            extent[0] = min(extent[0], chars.bottoms[index])
            extent[1] = max(extent[1], chars.tops[index])
    lines = _tabled(page.lines, words, rules or [])
    found = _Found(chars, shifts, unmapped, bars or [], tight)
    page.lines = _equations(lines, words[UPRIGHT], found)
    return page


_Boxes = Callable[[int], tuple[float, float, float, float] | None]


@dataclass(frozen=True)
class _Found:
    """What an equation is rebuilt from: the page's characters, its bars, and PDFium's tight box
    of a character (its loose one reaches past the letter: too coarse to place a script)."""

    chars: _Chars
    shifts: list[int]
    unmapped: list[bool]
    bars: list[Bar]
    tight: _Boxes | None = None


def _tight_boxes(textpage: object) -> _Boxes:
    rect = [ctypes.c_double() for _ in range(4)]
    pointers = [ctypes.byref(value) for value in rect]

    def box(index: int) -> tuple[float, float, float, float] | None:
        if not raw.FPDFText_GetCharBox(textpage, index, *pointers):
            return None
        left, right, bottom, top = (_finite(value.value) for value in rect)
        return (left, right, bottom, top) if right > left and top > bottom else None

    return box


def _equations(lines: list[Line], words: list[Word], found_on: _Found | None = None) -> list[Line]:
    """Each display equation's scattered lines, one block that keeps their layout, rebuilt as
    LaTeX when every piece of it is understood (015)."""
    placed = [
        Placed(line.text, line.top, line.bottom, line.size, line.right,
               bool(line.table or line.image or line.turn != UPRIGHT), line.left)
        for line in lines
    ]  # fmt: skip
    bars = [(bar.left, bar.right, bar.at) for bar in found_on.bars] if found_on else []
    for found in reversed(find_equations(placed, words, bars)):
        group = lines[found.start : found.stop]
        top, bottom = max(line.top for line in group), min(line.bottom for line in group)
        left, right = min(line.left for line in group), max(line.right for line in group)
        highest = max(group, key=lambda line: line.top)
        lowest = min(group, key=lambda line: line.bottom)
        # A font's boxes reach past its letters: never into the lines just above and below it
        # (across the equation, not a note beside it), never into its own first or last row.
        if found.start > 0:
            above = lines[found.start - 1]
            if above.left < right and above.right > left and bottom < above.bottom < top:
                top = max(above.bottom, highest.bottom)
        if found.stop < len(lines):
            below = lines[found.stop]
            if below.left < right and below.right > left and bottom < below.top < top:
                bottom = min(below.top, lowest.top)
        block = Line(
            "",
            0.0,  # a block, not text: never a footnote, a heading, a running line (review of 013)
            False,
            top,
            bottom,
            left=min(line.left for line in group),
            right=max(line.right for line in group),
            equation=_laid_out(group),
            latex=_latex(group, found_on, (bottom, top, left, right)) if found_on else "",
        )
        lines = [*lines[: found.start], block, *lines[found.stop :]]
    return lines


def _latex(group: list[Line], found: _Found, box: tuple[float, float, float, float]) -> str:
    """The equation's characters and the bars within its box, as LaTeX ("" when unsure)."""
    chars = found.chars
    glyphs: list[Glyph] = []
    for line in group:
        start, stop = line.span
        high = 0  # a character past U+FFFF comes as two halves (as ``_line`` reads them)
        for index in range(start, min(stop, len(chars.codes))):
            raw_code = chars.codes[index]
            if raw_code in _SKIPPED or raw_code == _LINE_END:
                continue
            font = chars.fonts[index]
            if found.unmapped[font] and not found.shifts[font]:
                return ""  # a font without a map: its letters are wrong (review of 015)
            code = _decoded(raw_code, found.shifts[font])
            if high and not 0xDC00 <= code < 0xE000:
                return ""  # a first half with no second: unreadable
            if 0xD800 <= code < 0xDC00:
                high = code
                continue
            if 0xDC00 <= code < 0xE000:
                if not high:
                    return ""
                code, high = 0x10000 + ((high - 0xD800) << 10) + (code - 0xDC00), 0
            if code in (0x09, 0x20):
                continue
            if code < 0x20 or code == 0x7F or code > 0x10FFFF or code == 0xFFFD:
                return ""  # unreadable, or a soft hyphen: never dropped unseen
            if code in _SOFT_HYPHENS:
                return ""
            if chars.rights[index] <= chars.lefts[index] or chars.turns[index] != UPRIGHT:
                return ""  # a character drawn nowhere, or turned: no place to read it from
            tight = found.tight(index) if found.tight is not None else None
            left, right, bottom, top = tight or (
                chars.lefts[index],
                chars.rights[index],
                chars.bottoms[index],
                chars.tops[index],
            )
            glyphs.append(
                Glyph(chr(code), left, right, bottom, top,
                      chars.font_sizes[index], chars.baselines[index])
            )  # fmt: skip
        if high:
            return ""  # a line that ends on a first half
    low, high_edge, left_edge, right_edge = box
    bars = [
        bar for bar in found.bars
        if low - 1 <= bar.at <= high_edge + 1
        and left_edge <= (bar.left + bar.right) / 2 <= right_edge
    ]  # fmt: skip
    return to_latex(glyphs, bars) or ""


def _laid_out(group: list[Line]) -> tuple[str, ...]:
    """The equation's rows, top first, each piece at its place (in half-letter columns)."""
    left = min(line.left for line in group)
    rows: list[list[Line]] = []
    for line in sorted(group, key=lambda line: (-line.bottom, line.left)):
        if rows and abs(rows[-1][0].bottom - line.bottom) <= ROW_SHARE * max(line.size, 1.0):
            rows[-1].append(line)
        else:
            rows.append([line])
    out = []
    for row in rows:
        text = ""
        for line in sorted(row, key=lambda line: line.left):
            column = round((line.left - left) / max(COLUMN_SHARE * line.size, 1.0))
            text = text.ljust(min(column, MAX_COLUMN)) + (
                " " if text and column <= len(text) else ""
            )
            text += line.text
        out.append(text.rstrip())
    return tuple(out)


def _cropped(page: object, line: Line, budget: list[int]) -> bytes | None:
    """The equation's place on the page, rendered: a PNG, or None (a turned or outsized page, a
    crop past the budget, nothing drawn there, a failure: its text is written instead)."""
    if raw.FPDFPage_GetRotation(page) != 0:
        return None
    height = _finite(raw.FPDF_GetPageHeightF(page))
    width = _finite(raw.FPDF_GetPageWidthF(page))
    if not (0 < width <= MAX_PAGE_POINTS and 0 < height <= MAX_PAGE_POINTS):
        return None  # past PDF's own limit: an offset ctypes cannot hold (review of 013)
    left, right = max(line.left - CROP_PAD, 0.0), min(line.right + CROP_PAD, width)
    bottom, top = max(line.bottom - CROP_PAD, 0.0), min(line.top + CROP_PAD, height)
    pixels_x, pixels_y = round((right - left) * CROP_SCALE), round((top - bottom) * CROP_SCALE)
    pixels = pixels_x * pixels_y
    if not 0 < pixels <= min(MAX_PICTURE_PIXELS, budget[0]):
        return None
    budget[0] -= pixels
    bitmap = raw.FPDFBitmap_Create(pixels_x, pixels_y, 0)
    if not bitmap:
        return None
    picture = pdfium.PdfBitmap.from_raw(bitmap)
    picture.warn_on_close = False  # closed only once the PNG is written from a copy of it
    try:
        raw.FPDFBitmap_FillRect(bitmap, 0, 0, pixels_x, pixels_y, 0xFFFFFFFF)
        raw.FPDF_RenderPageBitmap(
            bitmap,
            page,
            round(-left * CROP_SCALE),
            round(-(height - top) * CROP_SCALE),
            round(width * CROP_SCALE),
            round(height * CROP_SCALE),
            0,
            raw.FPDF_ANNOT,
        )
        trimmed = _trimmed(picture.to_pil().convert("RGB"))
        if trimmed is None:
            return None
        data = io.BytesIO()
        trimmed.save(data, "PNG")
        return data.getvalue()
    except (ValueError, OSError, MemoryError):
        return None
    finally:
        picture.close()


def _trimmed(image: Image.Image) -> Image.Image | None:
    """The equation's ink, a margin around it: a sliver of the line above or below, at the edge
    and apart from it, goes (a font's boxes reach far past its letters)."""
    ink = image.convert("L").point(lambda value: 255 if value < INK_LEVEL else 0)
    width, height = ink.size
    rows = [ink.crop((0, y, width, y + 1)).getbbox() is not None for y in range(height)]
    bands: list[list[int]] = []
    for y, inked in enumerate(rows):
        if inked and bands and y - bands[-1][1] <= APART_PIXELS:
            bands[-1][1] = y
        elif inked:
            bands.append([y, y])
    if len(bands) > 1 and bands[-1][1] == height - 1:
        bands.pop()  # the line below's top
    if len(bands) > 1 and bands[0][0] == 0:
        bands.pop(0)  # the line above's foot
    if not bands:
        return None  # no ink: nothing drawn there, the text says more
    box = ink.crop((0, bands[0][0], width, bands[-1][1] + 1)).getbbox()
    if box is None:
        return None
    left, right = max(box[0] - TRIM_MARGIN, 0), min(box[2] + TRIM_MARGIN, width)
    top, bottom = max(bands[0][0] - TRIM_MARGIN, 0), min(bands[-1][1] + 1 + TRIM_MARGIN, height)
    return image.crop((left, top, right, bottom))


def _goes_on(chars: _Chars, last: int, index: int, extent: list[float]) -> bool:
    """Whether a line PDFium ends goes on in the next one: the next character stands on the same
    row, right after the last (a subscript PDFium put on a line of its own: "Rᴺ" then "₊")."""
    following = next(
        (i for i in range(index + 1, min(index + LOOK_AHEAD, len(chars.codes)))
         if chars.codes[i] > 0x20 and chars.rights[i] > chars.lefts[i]),
        None,
    )  # fmt: skip
    if last < 0 or following is None:
        return False
    if chars.turns[last] != UPRIGHT or chars.turns[following] != UPRIGHT:
        return False
    low, high = extent  # the line's, not its last character's (a superscript, then a subscript)
    overlap = min(high, chars.tops[following]) - max(low, chars.bottoms[following])
    height = min(high - low, chars.tops[following] - chars.bottoms[following])
    size = max(chars.font_sizes[last], chars.font_sizes[following], 1.0)
    return (
        height > 0
        and overlap >= ROW_OVERLAP * height
        and chars.lefts[following] >= chars.lefts[last] - 1.0
        and chars.lefts[following] - chars.rights[last] <= SCRIPT_GAP_EMS * size
    )


def _new_row(chars: _Chars, last: int, index: int) -> bool:
    """A character turned otherwise than the last one (a page's header, then its sideways table's
    title), or a sideways one on another row: its row is across the page."""
    turn = chars.turns[index]
    if chars.codes[index] <= 0x20 or chars.rights[index] <= chars.lefts[index]:
        return False
    if ASLANT in (turn, chars.turns[last]):
        return False  # an aslant glyph in a line (a slanted symbol) stays in it (review of 013)
    if turn != chars.turns[last]:
        return True
    if turn not in (CLOCKWISE, COUNTERCLOCKWISE):
        return False
    height = max(_width(chars, index), _width(chars, last), 1.0)
    return abs(chars.lefts[index] - chars.lefts[last]) > NEW_ROW_SHARE * height


def _tabled(lines: list[Line], words: dict[int, list[Word]], rules: list[Rule]) -> list[Line]:
    """The lines a table found on the page covers give way to it, where its first one stood:
    ruled tables first (their words then taken), then the others by their aligned words. A table
    set sideways is found in its own frame (the page turned upright), then placed back."""
    for table, taken in find_lattices(rules, words[UPRIGHT]):
        box = (table.bottom, table.top, table.left, table.right)
        lines = _replaced(lines, table, UPRIGHT, box)
        gone = {id(word) for word in taken}
        words = {**words, UPRIGHT: [word for word in words[UPRIGHT] if id(word) not in gone]}
    for turn, turned in words.items():
        for table in find_tables(turned):
            # The table's box on the page: (bottom, top, left, right).
            box = {
                UPRIGHT: (table.bottom, table.top, table.left, table.right),
                CLOCKWISE: (-table.right, -table.left, table.bottom, table.top),
                COUNTERCLOCKWISE: (table.left, table.right, -table.top, -table.bottom),
            }[turn]
            lines = _replaced(lines, table, turn, box)
    return lines


def _replaced(
    lines: list[Line], table: Table, turn: int, box: tuple[float, float, float, float]
) -> list[Line]:
    low, high, left, right = box
    inside = [
        i for i, line in enumerate(lines)
        if line.turn == turn and not (line.table or line.image or line.equation)
        and line.bottom >= low - ROW_SLACK and line.top <= high + ROW_SLACK
        and line.left >= left - ROW_SLACK and line.right <= right + ROW_SLACK
    ]  # fmt: skip
    if inside:
        block = Line("", 0.0, False, high, low, table=table.rows, left=left, right=right)
        lines = [line for i, line in enumerate(lines) if i not in set(inside)]
        lines.insert(inside[0], block)
    return lines


def _line(
    chars: _Chars,
    span: range,
    shifts: list[int],
    unmapped: list[bool],
    document: Document,
    words: dict[int, list[Word]] | None = None,
) -> Line:
    pieces: list[tuple[str, int]] = []  # each piece of text and the character it comes from
    word: list[int] = []  # the indices of the word being read, and its text
    word_text: list[str] = []

    def put(piece: str, index: int = -1) -> None:
        pieces.append((piece, index))

    def end_word() -> None:
        turn = chars.turns[word[0]] if word else ASLANT
        if words is not None and turn in words and chars.turns[word[-1]] == turn:
            words[turn].append(_word("".join(word_text), chars, word, turn))
        word.clear()
        word_text.clear()

    high = 0  # PDFium gives a character past U+FFFF as two halves (a surrogate pair)
    visible: list[int] = []
    for index in span:
        font = chars.fonts[index]
        raw_code = chars.codes[index]
        if raw_code in _SKIPPED:
            continue
        if raw_code == _LINE_END:  # one PDFium ended where the row goes on: a space between
            put(" ")  # (gone if it touches a script: "Rᴺ" and "₊")
            end_word()
            continue
        code = _decoded(raw_code, shifts[font])
        if high and not 0xDC00 <= code < 0xE000:  # a first half with no second: unreadable
            document.unreadable += 1
            put(UNREADABLE)
            high = 0
        if 0xD800 <= code < 0xDC00:
            high = code
            continue
        if 0xDC00 <= code < 0xE000:
            if high:
                put(chr(0x10000 + ((high - 0xD800) << 10) + (code - 0xDC00)), index)
            else:
                document.unreadable += 1
                put(UNREADABLE, index)
            high = 0
            visible.append(index)
            word.append(index)
            word_text.append(pieces[-1][0])
            continue
        if code in _SOFT_HYPHENS:
            put(SOFT_HYPHEN, index)
        elif code == 0x09 or code == 0x20:
            put(" ")
            end_word()
            continue
        elif code < 0x20 or code == 0x7F or code > 0x10FFFF or code == 0xFFFD:
            # A code no map turned into a character: never dropped silently (ADR-0022).
            document.unreadable += 1
            put(UNREADABLE, index)
        elif unmapped[font] and not shifts[font]:
            document.unreadable += 1  # a font without a map, not read back: its letters are wrong
            put(chr(code), index)
        else:
            put(chr(code), index)
        visible.append(index)
        word.append(index)
        word_text.append(pieces[-1][0])
    if high:
        document.unreadable += 1
        put(UNREADABLE)
    end_word()
    shown = visible or list(span)
    sizes = Counter(round(chars.sizes[index], 1) for index in shown)
    return Line(
        " ".join(_scripted(pieces, chars, visible).split()),
        sizes.most_common(1)[0][0],
        sum(chars.bold[index] for index in shown) * 2 > len(shown),
        max(chars.tops[index] for index in shown),
        min(chars.bottoms[index] for index in shown),
        turn=Counter(chars.turns[index] for index in shown).most_common(1)[0][0],
        left=min(chars.lefts[index] for index in shown),
        right=max(chars.rights[index] for index in shown),
        span=(span.start, span.stop),
    )


def _scripted(pieces: list[tuple[str, int]], chars: _Chars, visible: list[int]) -> str:
    """The line's text, its sub- and superscripts written as such (014): a character smaller than
    the line's text, its baseline raised or lowered, as "EFᵗₒ", "Rᴺ₊", "zⱼ", a footnote's "²";
    a script with no such letter in Unicode as "^{…}" or "_{…}". The space PDFium puts around a
    script that touches its base goes."""
    marks = _scripts(chars, visible)
    if not marks:
        return "".join(piece for piece, _ in pieces)
    # Each piece's nearest drawn character before and after it: one pass each way (linear,
    # however many spaces a line holds; review of 014).
    before, after = [-1] * len(pieces), [-1] * len(pieces)
    last = -1
    for position, (_, index) in enumerate(pieces):
        before[position] = last
        if index >= 0:
            last = index
    last = -1
    for position in range(len(pieces) - 1, -1, -1):
        after[position] = last
        if pieces[position][1] >= 0:
            last = pieces[position][1]
    kept: list[tuple[str, int, str]] = []
    for position, (piece, index) in enumerate(pieces):
        if piece == " " and _hugs(before[position], after[position], marks, chars):
            continue
        kept.append((piece, index, marks.get(index, "")))
    out: list[str] = []
    run: list[str] = []
    mode = ""
    for piece, _, mark in [*kept, ("", -1, "")]:
        if mark != mode and run:
            out.append(_script_text(run, mode))
            run = []
        mode = mark
        if mark:
            run.append(piece)
        else:
            out.append(piece)
    return "".join(out)


def _scripts(chars: _Chars, visible: list[int]) -> dict[int, str]:
    """Each script's character and its kind: "^" raised, "_" lowered."""
    upright = [i for i in visible if chars.turns[i] == UPRIGHT and chars.font_sizes[i] > 0]
    if len(upright) < 2:
        return {}
    counts = Counter(round(chars.font_sizes[i], 1) for i in upright)
    commonest = counts.most_common(1)[0][0]
    # The text's size: the largest one many characters share ("((xᵗ⁺¹" has more script than
    # text), never a tall delimiter's.
    shared = [
        size for size, count in counts.items()
        if count >= max(2, TEXT_SHARE * len(upright)) and size <= DELIMITER_RATIO * commonest
    ]  # fmt: skip
    text_size = max(shared, default=commonest)
    # The text a script is set on: letters and digits of the text's size (never a "∑" or "=",
    # whose baseline is the symbol's own).
    level = {
        i for i in upright
        if abs(chars.font_sizes[i] - text_size) <= BASE_SHARE * text_size
        and (chr(chars.codes[i]).isalnum() or chr(chars.codes[i]) == ")")
    }  # fmt: skip
    normal = [i for i in upright if i in level]
    if not normal:
        return {}
    # Raised or lowered from the text it is set on, the character before it (or after): a PDFium
    # "line" may hold two rows of a paragraph, never one baseline. Found in one pass each way.
    previous: list[int | None] = []
    seen: int | None = None
    for i in upright:
        previous.append(seen)
        if i in level:
            seen = i
    following: list[int | None] = [None] * len(upright)
    seen = None
    for position in range(len(upright) - 1, -1, -1):
        following[position] = seen
        if upright[position] in level:
            seen = upright[position]
    small = [chars.font_sizes[i] < SCRIPT_SIZE * text_size for i in upright]
    marks: dict[int, str] = {}
    for position, i in enumerate(upright):
        if not small[position]:
            continue
        lone = (
            0 < position < len(upright) - 1 and not small[position - 1] and not small[position + 1]
        )
        if lone and not chr(chars.codes[i]).isalnum():
            continue  # an operator set smaller between two terms ("1 ∗ 0.169"), no script
        base = previous[position]
        if base is None:
            base = following[position]
        if base is None:
            base = normal[0]
        shift = chars.baselines[i] - chars.baselines[base]
        if shift > RAISED_EMS * text_size:
            marks[i] = "^"
        elif shift < -LOWERED_EMS * text_size:
            marks[i] = "_"
    return marks


def _hugs(before: int, after: int, marks: dict[int, str], chars: _Chars) -> bool:
    """A space between a script and what it is set on, narrower than a real one."""
    if before < 0 or after < 0 or not (before in marks or after in marks):
        return False
    gap = chars.lefts[after] - chars.rights[before]
    return gap < HUG_EMS * max(chars.font_sizes[before], chars.font_sizes[after], 1.0)


def _script_text(run: list[str], mode: str) -> str:
    table = _SUPERSCRIPTS if mode == "^" else _SUBSCRIPTS
    text = "".join(run)
    if all(char in table for char in text):
        return "".join(table[char] for char in text)
    return f"{mode}{{{text}}}"


def _word(text: str, chars: _Chars, indices: list[int], turn: int) -> Word:
    """A word's box in its frame: the page turned so its text reads upright (a clockwise turn
    takes the page's top to the frame's left)."""
    first, last = indices[0], indices[-1] + 1
    if last - first == len(indices):  # one run of characters, as nearly always: slices (fast)
        left, right = min(chars.lefts[first:last]), max(chars.rights[first:last])
        bottom, top = min(chars.bottoms[first:last]), max(chars.tops[first:last])
        if turn == UPRIGHT:
            return Word(text, left, right, bottom, top, max(chars.sizes[first:last]))
    else:
        left = min(chars.lefts[i] for i in indices)
        right = max(chars.rights[i] for i in indices)
        bottom = min(chars.bottoms[i] for i in indices)
        top = max(chars.tops[i] for i in indices)
    if turn == CLOCKWISE:
        return Word(text, -top, -bottom, left, right, max(_width(chars, i) for i in indices))
    if turn == COUNTERCLOCKWISE:
        return Word(text, bottom, top, -right, -left, max(_width(chars, i) for i in indices))
    return Word(text, left, right, bottom, top, max(chars.sizes[i] for i in indices))


def _width(chars: _Chars, index: int) -> float:
    return max(chars.rights[index] - chars.lefts[index], 0.0)
