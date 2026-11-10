"""What a PDF repeats on every page: running headers, footers and page numbers (008)."""

import math
import re
from collections import Counter

from clearmd.backend.services.conversion.pdf.cleaner.page_numbers import page_number
from clearmd.backend.services.conversion.pdf.cleaner.params import HEADING_RATIO, PARAGRAPH_GAP
from clearmd.backend.services.conversion.pdf.cleaner.render import is_block
from clearmd.backend.services.conversion.pdf.cleaner.sizes import size_key
from clearmd.backend.services.conversion.pdf.model import UPRIGHT, Line

EDGE_LINES = 3  # a running header or footer is among the first or last lines of a page
MIN_PAGES_FOR_RUNNING = 4  # fewer pages: only lines on every page are running ones
MIN_PAGES_FOR_SHORT = 2  # one page: nothing is taken for a running line
RUNNING_SHARE = 0.3  # on this share of the pages (odd and even pages often differ)
MIN_RUNNING_PAGES = 3
PLACE_POINTS = 6.0  # the same place on the page, within this
MARGIN_SHARE = 0.15  # a header or a footer lives in the top or bottom of the page


_DIGITS = re.compile(r"\d+")


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


RunningKey = tuple[str, int | None, int, float]  # text (or its shape), page offset, place, size


def _running_keys(line: Line, index: int) -> set[RunningKey]:
    """The same text at the same place, in the same size; with a number in it, the number is
    the same on every page ("2022") or follows the pages ("2 | Valencia", "Page 3"): "Table 4"
    on four pages is content."""
    place, size = round(line.top / PLACE_POINTS), size_key(line.size)
    keys: set[RunningKey] = {(" ".join(line.text.casefold().split()), None, place, size)}
    numbers = _DIGITS.findall(line.text)
    if numbers:
        keys.add((_shape(line.text), int(numbers[0][:6]) - index, place, size))
    return keys


def _in_margin(line: Line, height: float) -> bool:
    return line.bottom >= (1 - MARGIN_SHARE) * height or line.top <= MARGIN_SHARE * height


def without_running(
    pages: list[list[Line]], heights: list[float], body: float
) -> tuple[list[list[Line]], int]:
    """Each page's lines, without the ones repeated at the top or bottom of many pages and
    without the page numbers. A short document keeps everything; a line the size of a heading,
    or one whose text is also in the body of a page, is content."""
    with_text = sum(1 for lines in pages if lines)
    if with_text < MIN_PAGES_FOR_SHORT:
        return pages, 0
    # A letter of two or three pages: only what is on every one of them (ADR-0030 amended,
    # audit v4, B3-02); a longer document: on a share of its pages.
    short = with_text < MIN_PAGES_FOR_RUNNING
    threshold = with_text if short else max(MIN_RUNNING_PAGES, math.ceil(RUNNING_SHARE * with_text))
    seen: Counter[RunningKey] = Counter()
    in_body: set[str] = set()
    numbers: Counter[tuple[str, int]] = Counter()
    for page, lines in enumerate(pages):
        edges = _edges(lines)
        keys = set()
        for index, line in enumerate(lines):
            if is_block(line):
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
            found = page_number(lines[index].text)
            if found is not None and _in_margin(lines[index], heights[page]):
                numbers[found[0], found[1] - page] += 1
    running = {key for key, count in seen.items() if count >= threshold}
    running = {key for key in running if _shape(key[0]) not in in_body}
    # A run of page numbers is one at three pages already (the roman ii-viii of a front matter).
    numbering = {
        key
        for key, count in numbers.items()
        if count >= (with_text if short else MIN_RUNNING_PAGES)
    }
    kept: list[list[Line]] = []
    removed = 0
    for page, lines in enumerate(pages):
        if len(lines) == 1:  # a page's only line is its content, never its margin (audit v4)
            kept.append(lines)
            continue
        edges = _edges(lines)
        out = []
        for index, line in enumerate(lines):
            at_end = index in (0, len(lines) - 1) and _in_margin(line, heights[page])
            number = page_number(line.text) if at_end else None
            if is_block(line):
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
            elif line.turn != UPRIGHT and index in edges and _turned_running(line, page, running):
                removed += 1  # a page set sideways: its header is turned with it, elsewhere
            else:
                out.append(line)
        kept.append(out)
    return kept, removed


def _turned_running(line: Line, page: int, running: set[RunningKey]) -> bool:
    """The running line's text (and its page offset), wherever and however large it is."""
    texts = {key[:2] for key in running}
    return any(key[:2] in texts for key in _running_keys(line, page))
