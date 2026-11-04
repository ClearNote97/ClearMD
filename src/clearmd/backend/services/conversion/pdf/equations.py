"""Display equations in a PDF page, found by their number (feature 013, ADR-0034).

A displayed equation is set apart, with its number at the right margin: "(5)" alone on its row or
far from the formula before it. Its lines are the short ones of symbols around that number, up to
the prose before and after it. PDFium gives them as scattered pieces ("∑", "J", "j=1"); kept
together they are either cropped from the page as a picture (with the images folder, ADR-0033) or
written as a block that keeps their lines.

Pure: lines and words in, the equations' line ranges out.
"""

import bisect
import re
from collections.abc import Sequence
from dataclasses import dataclass

from clearmd.backend.services.conversion.pdf.tables import Word

LABEL = re.compile(r"\(\d{1,3}[a-z]?\)")  # (5), (12), (3a)
LABEL_SLACK = 24.0  # points: a number this close to the text's right edge is at the margin
LABEL_GAP_EMS = 2.0  # a number this far from the formula before it is set apart from it
ROW_EMS = 0.35  # words this close vertically are on one row (as tables.ROW_EMS)
GAP_EMS = 5.0  # a blank this tall (in line heights) above or below what is found ends it
MAX_LINES = 16  # an equation's lines at most: more is a page of formulas, not one
MAX_LABELS = 200  # equation numbers looked at on a page
MAX_ROW_WORDS = 400  # words looked at on a number's row
LINE_REACH = 40  # points: a line holding a number starts at most this far below it
TITLE_RATIO = 1.15  # a line this much larger than the equation's number is a heading
BAR_SHARE = 0.6  # of the text's width: a longer line is a rule, never a fraction's bar
BAR_EMS = 1.6  # a fraction's numerator and denominator stand this close to its bar (in sizes)
SCRIPT_SHARE = 0.9  # text this much smaller under a rule is a footnote
RULED_ROWS = 40.0  # points: the same rule this close above or below is a table's
_RELATION = re.compile(r"[=<>≤≥≠≈≡∈∉⊂⊆∼≃≅∝→⇒⇔]")
TITLE_LETTERS = 3  # if it has words: a tall "{" or "∑" alone is not
_CAPTION = re.compile(r"(?:Table|Tabla|Cuadro|Figure|Figura|Fig\.)\s+[0-9IVXLC]+\b")
_NUMBERED_HEADING = re.compile(r"\d{1,2}(?:\.\d{1,2})*\.?\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]")
PROSE_WORDS = 3  # a line with this many words of four letters or more is prose
_WORD = re.compile(r"\b[a-záéíóúüñ]{4,}\b")
# With no number to hold it, capitalised words make prose too ("Index", "Equation"); a numbered
# equation may name its variables so ("Profit = Revenue - Costs", review of 015).
_ANY_WORD = re.compile(r"\b[a-záéíóúüñ]{4,}\b", re.I)
# A line that starts a clause goes on the text: "where zj are …", "donde x es …".
_LEADS = re.compile(r"(?:where|donde|with|which|for|para|subject|sujeto)\s", re.I)  # not "y"


@dataclass(frozen=True)
class Placed:
    """What the equation finder needs of a line: its text and where it stands."""

    text: str
    top: float
    bottom: float
    size: float
    right: float
    other: bool  # a table, a picture, sideways text: never part of an equation
    left: float = 0.0


def find_equations(
    lines: list[Placed], words: list[Word], bars: Sequence[tuple[float, float, float]] | None = None
) -> list[range]:
    """The display equations of a page: ranges of its line indices, in reading order. Found by
    their number at the right margin, or (with no number, 015) by a fraction's bar: a short
    line drawn with words right above and below it, on lines that are no prose."""
    if not lines or not words:
        return []
    right_edge = max((line.right for line in lines if not line.other), default=None)
    if right_edge is None:  # a page of tables and pictures only
        return []
    taken: set[int] = set()
    found: list[range] = []
    labels = _label_lines(lines, words, right_edge)
    seeds = [(index, index, size, False) for index, size in sorted(labels.items())]
    seeds += [(*seed, True) for seed in _bar_lines(lines, words, bars or [], set(labels))]
    for first, last, size, unnumbered in seeds:
        if any(i in taken for i in range(first, last + 1)):
            continue
        stops = set(labels) | taken
        start, end = first, last
        # What is found so far, bottom to top, and the number's size (a subscript's is no measure).
        box = [
            min(line.bottom for line in lines[first : last + 1]),
            max(line.top for line in lines[first : last + 1]),
            size,
        ]
        while (
            start - 1 >= 0
            and first - start < MAX_LINES
            and _joins(lines[start - 1], start - 1, box, stops, unnumbered)
        ):
            start -= 1
        while (
            end + 1 < len(lines)
            and end - last < MAX_LINES
            and _joins(lines[end + 1], end + 1, box, stops, unnumbered)
        ):
            end += 1
        if end - start + 1 <= MAX_LINES:
            found.append(range(start, end + 1))
            taken.update(range(start, end + 1))
    return sorted(found, key=lambda lines_found: lines_found.start)


def _bar_lines(
    lines: list[Placed],
    words: list[Word],
    bars: Sequence[tuple[float, float, float]],
    labels: set[int],
) -> list[tuple[int, int, float]]:
    """The lines around each fraction's bar (left, right, height): words right above and right
    below it, within its ends; its lines are none of them prose, a table, a heading. As (first
    line, last line, the words' size), the page's bars at most ``MAX_LABELS``."""
    found: list[tuple[int, int, float]] = []
    text = [line for line in lines if not line.other]
    if not text:
        return found
    column = max(line.right for line in text) - min(line.left for line in text)
    ordered = sorted(words, key=lambda word: (word.bottom + word.top) / 2)
    middles = [(word.bottom + word.top) / 2 for word in ordered]
    bars = bars[:MAX_LABELS]
    by_ends: dict[tuple[int, int], list[float]] = {}
    for left, right, at in bars:
        by_ends.setdefault((round(left), round(right)), []).append(at)
    for left, right, at in bars:
        if right - left > BAR_SHARE * column:
            continue  # a rule across the text: a table's
        if sum(abs(other - at) <= RULED_ROWS for other in by_ends[(round(left), round(right))]) > 1:
            continue  # the same line again just above or below: a table's rows, ruled
        reach = BAR_EMS * 12.0
        low = bisect.bisect_left(middles, at - reach)
        high = bisect.bisect_right(middles, at + reach)
        near = [
            word for word in ordered[low:high][:MAX_ROW_WORDS]
            if left - 1 <= (word.left + word.right) / 2 <= right + 1
        ]  # fmt: skip
        size = max((word.size for word in near), default=0.0)
        above = [w for w in near if at < (w.bottom + w.top) / 2 <= at + BAR_EMS * size]
        below = [w for w in near if at - BAR_EMS * size <= (w.bottom + w.top) / 2 < at]
        if not above or not below:
            continue
        touched = [
            index for index, line in enumerate(lines)
            if not line.other and line.left < right and line.right > left
            and line.bottom <= at + BAR_EMS * size and line.top >= at - BAR_EMS * size
        ]  # fmt: skip
        if not touched or any(
            _prose(lines[index].text, True) or _titled(lines[index], size) for index in touched
        ):
            continue
        band = [w for w in ordered[low:high] if abs((w.bottom + w.top) / 2 - at) <= size]
        if any(w.left < x - 1 and w.right > x + 1 for w in band for x in (left, right)):
            continue  # a word across its end: a rule under a line, not a fraction's bar
        if abs(left - min(line.left for line in text)) <= 2 and max(
            w.size for w in below
        ) < SCRIPT_SHARE * max(w.size for w in above):
            continue  # at the column's start, smaller text under it: the footnotes' rule
        if not any(_RELATION.search(lines[index].text) for index in touched):
            continue  # "N" over "45" in a table: an equation says what equals what
        first, last = min(touched), max(touched)
        if last - first < MAX_LINES and not any(i in labels for i in range(first, last + 1)):
            found.append((first, last, size))
    return found


def _label_lines(lines: list[Placed], words: list[Word], right_edge: float) -> dict[int, float]:
    """The lines that hold an equation's number, set apart at the right margin: the words sorted
    once, each number's row found by bisection; a page's numbers at most ``MAX_LABELS``. Each
    with the number's own size (its line may be mostly scripts)."""
    candidates = [
        word for word in words
        if LABEL.fullmatch(word.text) and word.right >= right_edge - LABEL_SLACK
    ][:MAX_LABELS]  # fmt: skip
    if not candidates:
        return {}
    ordered = sorted(words, key=lambda w: w.bottom)
    bottoms = [word.bottom for word in ordered]
    by_bottom: dict[float, list[int]] = {}
    for index, line in enumerate(lines):
        if not line.other:
            by_bottom.setdefault(round(line.bottom), []).append(index)
    labels: dict[int, float] = {}
    for word in candidates:
        reach = ROW_EMS * word.size
        low = bisect.bisect_left(bottoms, word.bottom - reach)
        high = bisect.bisect_right(bottoms, word.bottom + reach)
        before = max(
            (other.right for other in ordered[low:high][:MAX_ROW_WORDS]
             if other is not word and other.right <= word.left),
            default=None,
        )  # fmt: skip
        if before is not None and word.left - before < LABEL_GAP_EMS * word.size:
            continue  # "… as in (5)": a reference at the end of a line of prose
        for key in range(round(word.bottom) - LINE_REACH, round(word.bottom) + 2):
            for index in by_bottom.get(key, []):
                line = lines[index]
                holds = line.bottom <= word.bottom + 1 and line.top >= word.top - 1
                if holds and line.text.endswith(word.text):
                    labels[index] = max(word.size, line.size)
    return labels


def _joins(
    line: Placed, index: int, box: list[float], stops: set[int], unnumbered: bool = False
) -> bool:
    """Whether the line is one of the equation's: a line of symbols near what is found (its
    number may stand halfway down it); ``box`` grows with it. A heading or a caption is not."""
    if index in stops or line.other or _prose(line.text, unnumbered) or _titled(line, box[2]):
        return False
    reach = GAP_EMS * max(line.size, box[2], 1.0)
    if line.bottom - box[1] > reach or box[0] - line.top > reach:
        return False
    box[0], box[1] = min(box[0], line.bottom), max(box[1], line.top)
    return True


def _titled(line: Placed, size: float) -> bool:
    """A heading ("3. Methods", or words larger than the equation's number) or a caption. A tall
    brace, bracket or sum is the equation's own: no words (v0.8.0 cut equations there)."""
    text = line.text.strip()
    return (
        (line.size > TITLE_RATIO * size and sum(char.isalpha() for char in text) >= TITLE_LETTERS)
        or _CAPTION.match(text) is not None
        or _NUMBERED_HEADING.match(text) is not None
    )


def _prose(text: str, any_case: bool = False) -> bool:
    """A line of sentences: several words, or one that leads into what follows ("as follows:")."""
    stripped = text.strip()
    return (
        len((_ANY_WORD if any_case else _WORD).findall(stripped)) >= PROSE_WORDS
        or stripped.endswith(":")
        or _LEADS.match(stripped) is not None
    )
