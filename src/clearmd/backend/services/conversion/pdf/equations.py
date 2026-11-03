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
TITLE_LETTERS = 3  # if it has words: a tall "{" or "∑" alone is not
_CAPTION = re.compile(r"(?:Table|Tabla|Cuadro|Figure|Figura|Fig\.)\s+[0-9IVXLC]+\b")
_NUMBERED_HEADING = re.compile(r"\d{1,2}(?:\.\d{1,2})*\.?\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]")
PROSE_WORDS = 3  # a line with this many words of four letters or more is prose
_WORD = re.compile(r"\b[a-záéíóúüñ]{4,}\b")
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


def find_equations(lines: list[Placed], words: list[Word]) -> list[range]:
    """The display equations of a page: ranges of its line indices, in reading order."""
    if not lines or not words:
        return []
    right_edge = max((line.right for line in lines if not line.other), default=None)
    if right_edge is None:  # a page of tables and pictures only
        return []
    taken: set[int] = set()
    found: list[range] = []
    labels = _label_lines(lines, words, right_edge)
    for index in sorted(labels):
        if index in taken:
            continue
        stops = set(labels) | taken
        start, end = index, index
        # What is found so far, bottom to top, and the number's size (a subscript's is no measure).
        box = [lines[index].bottom, lines[index].top, labels[index]]
        while (
            start - 1 >= 0
            and index - start < MAX_LINES
            and _joins(lines[start - 1], start - 1, box, stops)
        ):
            start -= 1
        while (
            end + 1 < len(lines)
            and end - index < MAX_LINES
            and _joins(lines[end + 1], end + 1, box, stops)
        ):
            end += 1
        if end - start + 1 <= MAX_LINES:
            found.append(range(start, end + 1))
            taken.update(range(start, end + 1))
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


def _joins(line: Placed, index: int, box: list[float], stops: set[int]) -> bool:
    """Whether the line is one of the equation's: a line of symbols near what is found (its
    number may stand halfway down it); ``box`` grows with it. A heading or a caption is not."""
    if index in stops or line.other or _prose(line.text) or _titled(line, box[2]):
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


def _prose(text: str) -> bool:
    """A line of sentences: several words, or one that leads into what follows ("as follows:")."""
    stripped = text.strip()
    return (
        len(_WORD.findall(stripped)) >= PROSE_WORDS
        or stripped.endswith(":")
        or _LEADS.match(stripped) is not None
    )
