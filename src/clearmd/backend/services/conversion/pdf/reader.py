"""PDFium reads the text: lines with their size, weight and place (feature 008, ADR-0030).

PDFium keeps the spaces that pdfminer loses in many papers ("interactionsbasedonvalues"), and
reads rotated text the right way round. A font without a usable character map gives its glyph
codes instead of letters ("(6&8(/$" for "ESCUELA"): when PDFium says a font has no map, and its
codes are letters moved by one distance, with the space moved to a control character, the font is
read back (``shift``). What still cannot be read is shown as "�" and counted.

PDFium's own C API is called (pypdfium2's raw bindings): ClearMD opens the document itself, so a
load error is read when it happens, and a PDF without pages is an empty document.
"""

import math
from collections import Counter
from dataclasses import dataclass

import pypdfium2.raw as raw

from clearmd.backend.services.conversion.images import ImageSink
from clearmd.backend.services.conversion.pdf.decode import (
    LINE_END,
    SKIPPED,
    SOFT_HYPHENS,
    decoded,
    shift,
)
from clearmd.backend.services.conversion.pdf.equations import Placed, find_equations
from clearmd.backend.services.conversion.pdf.latex import Bar, Glyph, to_latex
from clearmd.backend.services.conversion.pdf.lattice import Rule, find_lattices
from clearmd.backend.services.conversion.pdf.model import (
    ASLANT,
    CLOCKWISE,
    COUNTERCLOCKWISE,
    SOFT_HYPHEN,
    UNREADABLE,
    UPRIGHT,
    Boxes,
    Chars,
    Document,
    Line,
    Page,
)
from clearmd.backend.services.conversion.pdf.pdfium.crop import pictured
from clearmd.backend.services.conversion.pdf.pdfium.document import text_pages
from clearmd.backend.services.conversion.pdf.pdfium.fonts import MAX_PAGE_CHARS, Fonts, count
from clearmd.backend.services.conversion.pdf.pdfium.page_chars import page_chars, tight_boxes
from clearmd.backend.services.conversion.pdf.pdfium.page_objects import page_rules
from clearmd.backend.services.conversion.pdf.pdfium.pictures import pictures, placed
from clearmd.backend.services.conversion.pdf.tables import Table, Word, find_tables

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
            else _page(chars, shifts, unmapped, result, rules, bars, tight_boxes(textpage))
        )
        if images is not None and handle is not None:
            page.lines = [pictured(handle, line, images, budget) for line in page.lines]
            page.lines = placed(page.lines, pictures(document, handle, images, budget))
        page.height = height
        result.pages.append(page)
    return result


def _page(
    chars: Chars,
    shifts: list[int],
    unmapped: list[bool],
    document: Document,
    rules: list[Rule] | None = None,
    bars: list[Bar] | None = None,
    tight: "Boxes | None" = None,
) -> Page:
    page = Page()
    words: dict[int, list[Word]] = {UPRIGHT: [], CLOCKWISE: [], COUNTERCLOCKWISE: []}
    start = 0
    last = -1  # the last character drawn (with a width): where a sideways row goes on from
    extent = [math.inf, -math.inf]  # the line's bottom and top so far
    for index in range(len(chars.codes) + 1):
        ended = index == len(chars.codes) or (
            chars.codes[index] == LINE_END and not _goes_on(chars, last, index, extent)
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


@dataclass(frozen=True)
class _Found:
    """What an equation is rebuilt from: the page's characters, its bars, and PDFium's tight box
    of a character (its loose one reaches past the letter: too coarse to place a script)."""

    chars: Chars
    shifts: list[int]
    unmapped: list[bool]
    bars: list[Bar]
    tight: Boxes | None = None


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
            if raw_code in SKIPPED or raw_code == LINE_END:
                continue
            font = chars.fonts[index]
            if found.unmapped[font] and not found.shifts[font]:
                return ""  # a font without a map: its letters are wrong (review of 015)
            code = decoded(raw_code, found.shifts[font])
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
            if code in SOFT_HYPHENS:
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


def _goes_on(chars: Chars, last: int, index: int, extent: list[float]) -> bool:
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


def _new_row(chars: Chars, last: int, index: int) -> bool:
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
    chars: Chars,
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
        if raw_code in SKIPPED:
            continue
        if raw_code == LINE_END:  # one PDFium ended where the row goes on: a space between
            put(" ")  # (gone if it touches a script: "Rᴺ" and "₊")
            end_word()
            continue
        code = decoded(raw_code, shifts[font])
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
        if code in SOFT_HYPHENS:
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


def _scripted(pieces: list[tuple[str, int]], chars: Chars, visible: list[int]) -> str:
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


def _scripts(chars: Chars, visible: list[int]) -> dict[int, str]:
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


def _hugs(before: int, after: int, marks: dict[int, str], chars: Chars) -> bool:
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


def _word(text: str, chars: Chars, indices: list[int], turn: int) -> Word:
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


def _width(chars: Chars, index: int) -> float:
    return max(chars.rights[index] - chars.lefts[index], 0.0)
