"""From PDFium's lines to Markdown: what a PDF repeats on every page goes, paragraphs and words
broken across lines are joined, headings are told by their size (feature 008, ADR-0030).

Only text: no OCR, no tables rebuilt, no images, one reading order (PDFium's: a page in columns
may be read across). Every piece of document text is escaped (ADR-0023); the block lines ClearMD
writes itself (headings, list items) carry ``MARK``, and what follows a list marker is
neutralized like any other line.
"""

import math
import re
from collections import Counter
from dataclasses import dataclass, field

from clearmd.backend.services.conversion.markdown_out import (
    MARK,
    escape_text,
    heading_text,
    link_target,
    neutralize,
    tidy,
)
from clearmd.backend.services.conversion.pdf.reader import SOFT_HYPHEN, Document, Line

EDGE_LINES = 3  # a running header or footer is among the first or last lines of a page
MIN_PAGES_FOR_RUNNING = 4  # fewer pages: nothing is taken for a running line
RUNNING_SHARE = 0.3  # on this share of the pages (odd and even pages often differ)
MIN_RUNNING_PAGES = 3
PLACE_POINTS = 6.0  # the same place on the page, within this
MARGIN_SHARE = 0.15  # a header or a footer lives in the top or bottom of the page
HEADING_RATIO = 1.2  # this much taller than the body text
HEADING_TEXT_SHARE = 0.15  # a size holding more of the text than this is text, not headings
MAX_HEADING_CHARS = 150
MAX_HEADING_LINES = 3  # a heading wrapped on several lines is one heading; more is a paragraph
MAX_LEVEL = 4
PARAGRAPH_GAP = 0.8  # a blank this many line heights tall starts a paragraph
FOOTNOTE_RATIO = 0.9  # the small lines at the foot of a page, under its text: its footnotes
SIZE_CHANGE = 0.1  # text this much larger or smaller is another block (a caption, a note)
MIN_LETTER_SHARE = 0.6  # a heading is words: a formula in a large font is not one

_DIGITS = re.compile(r"\d+")
# A page number, alone on the first or last line: "7", "- 7 -", "Page 7 of 20", "xii".
_PAGE_NUMBER = re.compile(
    r"[-–—|·\s]*(?:(?:page|p[áa]g(?:ina)?\.?|p\.)\s*)?(\d{1,4}|[ivxlcdm]{1,7})"
    r"(?:\s*(?:/|of|de)\s*\d{1,4})?[-–—|·\s]*",
    re.IGNORECASE,
)
_ROMAN = re.compile(r"m{0,3}(cm|cd|d?c{0,3})(xc|xl|l?x{0,3})(ix|iv|v?i{0,3})")
_ROMAN_VALUES = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}
# "2 Methodology", "3.1 Data", "IV. RESULTADOS": numbered, then a capital (or "¿").
_NUMBERED = re.compile(r"(?:(\d{1,2}(?:\.\d{1,2}){0,3})\.?|([IVXL]{1,5})\.)\s+[A-ZÁÉÍÓÚÑ¿]")
_INSIDE_SENTENCE = re.compile(r"[.?!]\s+\S|=")
_NOTE_START = re.compile(r"(?:\d{1,3}|[*†‡§])\s*\S")
_BULLET = re.compile(r"[•●▪■◦‣∙·](?=\s)\s*")  # always a list item
_DASH = re.compile(r"[-–*](?=\s)\s*")  # an item only where no sentence goes on
_CIRCLE = re.compile(r"o(?=\s)\s*")  # Word's second-level bullet, only inside a list
_SENTENCE_END = re.compile(r"[.!?:;…\"”»)]$")


@dataclass
class Cleaned:
    markdown: str
    running_removed: int = 0  # header, footer and page-number lines left out
    headings: int = 0
    empty_pages: list[int] = field(default_factory=list)  # 1-based: no text (scanned?)


def _shape(text: str) -> str:
    """A running line with its page number or date in it is still the same line."""
    return " ".join(_DIGITS.sub("#", text).casefold().split())


def _edges(lines: list[Line]) -> set[int]:
    count = len(lines)
    return set(range(min(EDGE_LINES, count))) | set(range(max(count - EDGE_LINES, 0), count))


def _apart(lines: list[Line], index: int) -> bool:
    """A header or a footer stands apart from the text: a blank between it and the body (a
    caption, a "Source:" line, sits right against its table; code review of 008)."""
    count = len(lines)
    if index < EDGE_LINES:
        pairs = range(index, min(EDGE_LINES, count - 1))
    else:
        pairs = range(max(count - EDGE_LINES, 1) - 1, index)
    for upper in pairs:
        line, below = lines[upper], lines[upper + 1]
        if line.bottom - below.top >= PARAGRAPH_GAP * max(min(line.size, below.size), 1.0):
            return True
    return False


def _size_key(size: float) -> float:
    return round(size * 2) / 2


def _body_size(pages: list[list[Line]]) -> float:
    sizes: Counter[float] = Counter()
    for lines in pages:
        for line in lines:
            sizes[_size_key(line.size)] += len(line.text)
    return sizes.most_common(1)[0][0] if sizes else 0.0


def _roman(text: str) -> int | None:
    lowered = text.lower()
    if not lowered or not _ROMAN.fullmatch(lowered):
        return None
    total = 0
    for index, char in enumerate(lowered):
        value = _ROMAN_VALUES[char]
        following = _ROMAN_VALUES[lowered[index + 1]] if index + 1 < len(lowered) else 0
        total += -value if value < following else value
    return total


def _page_number(text: str) -> tuple[str, int] | None:
    """("arabic" or "roman", the number) when the line is only a page number."""
    found = _PAGE_NUMBER.fullmatch(text)
    if found is None:
        return None
    value = found.group(1)
    if value.isdigit():
        return "arabic", int(value)
    number = _roman(value)
    return ("roman", number) if number else None


RunningKey = tuple[str, int | None, int, float]  # text (or its shape), page offset, place, size


def _running_keys(line: Line, index: int) -> set[RunningKey]:
    """The same text at the same place, in the same size; with a number in it, the number is
    the same on every page ("2022") or follows the pages ("2 | Valencia", "Page 3"): "Table 4"
    on four pages is content."""
    place, size = round(line.top / PLACE_POINTS), _size_key(line.size)
    keys: set[RunningKey] = {(" ".join(line.text.casefold().split()), None, place, size)}
    numbers = _DIGITS.findall(line.text)
    if numbers:
        keys.add((_shape(line.text), int(numbers[0][:6]) - index, place, size))
    return keys


def _in_margin(line: Line, height: float) -> bool:
    return line.bottom >= (1 - MARGIN_SHARE) * height or line.top <= MARGIN_SHARE * height


def _without_running(
    pages: list[list[Line]], heights: list[float], body: float
) -> tuple[list[list[Line]], int]:
    """Each page's lines, without the ones repeated at the top or bottom of many pages and
    without the page numbers. A short document keeps everything; a line the size of a heading,
    or one whose text is also in the body of a page, is content."""
    with_text = sum(1 for lines in pages if lines)
    if with_text < MIN_PAGES_FOR_RUNNING:
        return pages, 0
    threshold = max(MIN_RUNNING_PAGES, math.ceil(RUNNING_SHARE * with_text))
    seen: Counter[RunningKey] = Counter()
    in_body: set[str] = set()
    numbers: Counter[tuple[str, int]] = Counter()
    for page, lines in enumerate(pages):
        edges = _edges(lines)
        keys = set()
        for index, line in enumerate(lines):
            if line.image:
                continue  # a picture is never a running line: a logo stays (review of 012)
            if index not in edges:
                in_body.add(_shape(line.text))
            elif (
                (not body or line.size < HEADING_RATIO * body)
                and _in_margin(line, heights[page])
                and _apart(lines, index)
            ):
                keys |= _running_keys(line, page)
        seen.update(keys)
        for index in {0, len(lines) - 1} if lines else set():
            found = _page_number(lines[index].text)
            if found is not None and _in_margin(lines[index], heights[page]):
                numbers[found[0], found[1] - page] += 1
    running = {key for key, count in seen.items() if count >= threshold}
    running = {key for key in running if _shape(key[0]) not in in_body}
    # A run of page numbers is one at three pages already (the roman ii-viii of a front matter).
    numbering = {key for key, count in numbers.items() if count >= MIN_RUNNING_PAGES}
    kept: list[list[Line]] = []
    removed = 0
    for page, lines in enumerate(pages):
        edges = _edges(lines)
        out = []
        for index, line in enumerate(lines):
            at_end = index in (0, len(lines) - 1) and _in_margin(line, heights[page])
            number = _page_number(line.text) if at_end else None
            if line.image:
                out.append(line)
            elif number is not None and (number[0], number[1] - page) in numbering:
                removed += 1
            elif (
                index in edges
                and _in_margin(line, heights[page])
                and _apart(lines, index)
                and _running_keys(line, page) & running
            ):
                removed += 1
            else:
                out.append(line)
        kept.append(out)
    return kept, removed


def _heading_like(line: Line) -> bool:
    """Words, not too long, no sentence's end ("II. MARCO TEÓRICO." in capitals may end so)."""
    text = line.text
    visible = [char for char in text if not char.isspace()]
    letters = sum(char.isalpha() for char in visible)
    return (
        len(text) <= MAX_HEADING_CHARS
        and letters >= 3
        and letters >= MIN_LETTER_SHARE * len(visible)
        and (not text.endswith((".", ",", ";")) or (text.endswith(".") and text.isupper()))
        and "=" not in text
    )


def _levels(pages: list[list[Line]], body: float) -> dict[float, int]:
    """Each heading size its level, the tallest first; a size that holds much of the text is a
    larger body, not headings."""
    if not body:
        return {}
    weight: Counter[float] = Counter()
    total = 0
    for lines in pages:
        for line in lines:
            weight[_size_key(line.size)] += len(line.text)
            total += len(line.text)
    sizes = sorted(
        {
            _size_key(line.size)
            for lines in pages
            for line in lines
            if line.size >= HEADING_RATIO * body
            and _heading_like(line)
            and weight[_size_key(line.size)] <= HEADING_TEXT_SHARE * total
        },
        reverse=True,
    )
    return {size: min(rank + 1, MAX_LEVEL) for rank, size in enumerate(sizes)}


def _joined(parts: list[str]) -> str:
    """The lines of one block as one text; built once, whatever its length."""
    pieces: list[str] = []
    for part in parts:
        if not pieces:
            pieces.append(part)
            continue
        previous = pieces[-1]
        if previous.endswith(SOFT_HYPHEN):
            # A word broken at the end of the line; before a capital it was a real hyphen
            # ("socio-Economic"), which PDFium also gives as a broken word.
            pieces[-1] = previous[:-1] + ("-" if part[:1].isupper() else "")
            pieces.append(part)
        elif previous.endswith("-") and previous[-2:-1].isalnum() and part[:1].isalnum():
            pieces.append(part)  # "2012-" + "2016": the hyphen stays, the two are one again
        else:
            pieces.append(" ")
            pieces.append(part)
    return _SOFT_INSIDE.sub(_unbroken, "".join(pieces)).replace(SOFT_HYPHEN, "")


_SOFT_INSIDE = re.compile(SOFT_HYPHEN + r"(?=(\w))")


def _unbroken(found: re.Match[str]) -> str:
    """A word PDFium joined itself: before a capital it was a real hyphen ("socio-Economic");
    before a small letter, a hyphenation (also "well-known" then reads "wellknown": PDFium
    cannot tell them apart, and the broken word is by far the commoner)."""
    return "-" if found.group(1).isupper() else ""


def _resized(last: Line, line: Line) -> bool:
    return abs(line.size - last.size) > SIZE_CHANGE * max(last.size, line.size, 1.0)


class _Writer:
    """Blocks in order: headings, list items and paragraphs, each one Markdown block."""

    def __init__(self, body: float, levels: dict[float, int]) -> None:
        self._body = body
        self._levels = levels
        self.blocks: list[str] = []
        self._kind = ""  # "", "heading", "item", "text"
        self._parts: list[str] = []
        self._last: Line | None = None
        self._level = 0
        self._typical = 80.0  # a full line's length on this page, in characters
        self._held: list[str] = []  # footnotes, written once the paragraph they cut ends
        self.headings = 0

    # --- Blocks ----------------------------------------------------------------------------

    def _flush(self) -> None:
        if not self._parts:
            self._kind = ""
            return
        text = escape_text(_joined(self._parts))
        if self._kind == "heading":
            self.blocks.append(f"{MARK}{'#' * self._level} {heading_text(text)}")
            self.headings += 1
        elif self._kind == "item":
            # "• # x" is no heading in an item (security audit of 008): what follows the
            # marker is neutralized like any line, its indentation (marks removed) dropped.
            self.blocks.append(f"{MARK}- " + neutralize(text.lstrip(), keep_marks=True))
        else:
            self.blocks.append(text)
        ended = self._kind != "text" or bool(_SENTENCE_END.search(self._parts[-1]))
        kind = self._kind
        self._parts = []
        self._kind = ""
        if kind != "heading" and ended:
            self._release()

    def _release(self) -> None:
        self.blocks.extend(self._held)
        self._held = []

    def hold(self, notes: list[Line]) -> None:
        """A page's footnotes: one block each, after the paragraph the page break cut."""
        parts: list[str] = []
        for line in notes:
            if parts and _NOTE_START.match(line.text):
                self._held.append(escape_text(_joined(parts)))
                parts = []
            parts.append(line.text)
        if parts:
            self._held.append(escape_text(_joined(parts)))
        if not self._parts:  # nothing waits for the next page: they go now
            self._release()

    def page_break(self) -> None:
        """A paragraph goes on to the next page only when its sentence does; a heading or a list
        item ends with its page."""
        ended = self._parts and _SENTENCE_END.search(self._parts[-1])
        if self._kind == "heading" or ended:
            self._flush()
        self._last = None

    # --- Lines -----------------------------------------------------------------------------

    def add(self, line: Line) -> None:
        if line.image:  # a picture: its own block, where it stands on the page (012)
            self._flush()  # after the text above it ("Figure 1 - Sales by region")
            self.blocks.append(f"{MARK}![]({link_target(line.image)})")
            return
        gap = self._gap(line)
        last = self._last
        resized = last is not None and _resized(last, line)
        level = self._heading_level(line, gap)
        if self._kind == "text" and self._grown and not gap and not resized:
            self._parts.append(line.text)  # a paragraph in a larger font goes on
        elif self._numbered and self._cut_sentence(line, gap, resized):
            self._kind, self._numbered = "text", False  # "15 Juzgados … que" + "completan": text
            self._grown = False
            self._parts.append(line.text)
        elif level:
            self._heading(line, level, gap)
        elif self._heading_goes_on(line, gap, resized):
            self._parts.append(line.text)
        elif item := self._item(line):
            self._flush()
            self._kind = "item"
            self._parts.append(item)
        else:
            lower = line.text[:1].islower()
            new = self._parts and not lower and self._ended()
            ends_item = self._kind == "item" and not lower  # an item goes on only in lowercase
            if self._kind in {"heading", ""} or gap or resized or new or ends_item:
                self._flush()
            if not self._kind:
                self._kind = "text"
                self._grown = False
            self._parts.append(line.text)
        self._last = line

    _grown = False  # the paragraph started as a heading: a larger font, too long for one
    _numbered = False  # the heading came from a bold number, not from its size

    def _heading(self, line: Line, level: int, gap: bool) -> None:
        same = self._kind == "heading" and level == self._level and not gap
        if same and len(self._parts) >= MAX_HEADING_LINES:
            self._kind, self._grown = "text", True  # four lines: a paragraph, not a heading
            self._parts.append(line.text)
            return
        if not same:
            self._flush()
            self._release()  # footnotes before a heading, never between it and its text
            self._kind, self._level = "heading", level
            self._numbered = self._levels.get(_size_key(line.size)) is None
        self._parts.append(line.text)

    def _cut_sentence(self, line: Line, gap: bool, resized: bool) -> bool:
        """The line after a bold numbered "heading" goes on in lowercase, close and in the same
        size: that was the start of a sentence, not a heading (adversarial check of 008)."""
        return (
            self._kind == "heading"
            and not gap
            and not resized
            and line.text[:1].islower()
            and not line.bold
        )

    def _heading_goes_on(self, line: Line, gap: bool, resized: bool) -> bool:
        """The second line of a bold numbered heading: bold too, same size, close, after a first
        line that filled the width or before one in lowercase (a short heading is whole; the bold
        line after it is text)."""
        last = self._last
        return (
            self._kind == "heading"
            and last is not None
            and last.bold
            and (not self._short(last) or line.text[:1].islower())  # or it goes on in lowercase
            and line.bold
            and not gap
            and not resized
            and len(self._parts) < MAX_HEADING_LINES
            and _heading_like(line)
        )

    def _item(self, line: Line) -> str | None:
        text = line.text
        if bullet := _BULLET.match(text):
            return text[bullet.end() :]
        mid_sentence = self._kind == "text" and not self._ended_sentence()
        if (dash := _DASH.match(text)) and not mid_sentence:
            return text[dash.end() :]
        if (circle := _CIRCLE.match(text)) and self._kind == "item":
            return text[circle.end() :]
        return None

    def _ended_sentence(self) -> bool:
        return bool(self._parts) and bool(_SENTENCE_END.search(self._parts[-1]))

    def _ended(self) -> bool:
        """The previous line ended a sentence and the next one starts a new one with a capital:
        a paragraph ends there only if that line was short (the rest of it was left blank)."""
        last = self._last
        return last is not None and bool(_SENTENCE_END.search(last.text)) and self._short(last)

    def _short(self, line: Line) -> bool:
        return len(line.text) < 0.6 * self._typical

    def set_typical(self, lines: list[Line]) -> None:
        lengths = sorted(len(line.text) for line in lines)
        self._typical = float(lengths[len(lengths) * 3 // 4]) if lengths else 80.0

    def _gap(self, line: Line) -> bool:
        last = self._last
        if last is None:
            return False
        height = max(min(last.size, line.size), 1.0)
        blank = last.bottom - line.top
        return blank > PARAGRAPH_GAP * height or line.top > last.top + height  # or a new column

    def _heading_level(self, line: Line, gap: bool) -> int:
        if not _heading_like(line):
            return 0
        found = self._levels.get(_size_key(line.size))
        if found:
            return found
        numbered = _NUMBERED.match(line.text)
        # A bold number starts a heading only where a block may start: a page's top, a blank,
        # after a sentence's end or another block; never in the middle of a paragraph.
        starts = self._last is None or gap or self._kind != "text" or self._ended_sentence()
        if (
            not starts
            or not line.bold
            or numbered is None
            or len(line.text) > 90
            or _INSIDE_SENTENCE.search(line.text, numbered.end())
        ):
            return 0
        arabic = numbered.group(1)
        return min(arabic.count(".") + 2, MAX_LEVEL) if arabic else 2

    def finish(self) -> str:
        self._flush()
        self._release()
        return "\n\n".join(self.blocks)


def _footnotes(lines: list[Line], body: float) -> tuple[list[Line], list[Line]]:
    """The page's text, and the small lines under it (its footnotes)."""
    start = len(lines)
    while (
        start > 0 and not lines[start - 1].image and lines[start - 1].size < FOOTNOTE_RATIO * body
    ):
        start -= 1
    if start == 0 or start == len(lines) or not body:
        return lines, []
    return lines[:start], lines[start:]


def clean(document: Document) -> Cleaned:
    pages = [page.lines for page in document.pages]
    body = _body_size(pages)
    heights = [page.height for page in document.pages]
    pages, removed = _without_running(pages, heights, body)
    body = _body_size(pages) or body
    writer = _Writer(body, _levels(pages, body))
    # A page with only a header or a number left (a scan with a printed folio) has no text.
    empty = [number for number, lines in enumerate(pages, start=1) if not lines]
    for lines in pages:
        text, notes = _footnotes(lines, body)
        writer.set_typical(text)
        for line in text:
            writer.add(line)
        writer.page_break()
        if notes:
            writer.hold(notes)
    markdown = tidy(neutralize(writer.finish()))
    return Cleaned(markdown, removed, writer.headings, empty)
