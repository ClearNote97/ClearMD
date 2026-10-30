"""Display equations in a PDF page, found by their number (feature 013, ADR-0034).

A displayed equation is set apart, with its number at the right margin: "(5)" alone on its row or
far from the formula before it. Its lines are the short ones of symbols around that number, up to
the prose before and after it. PDFium gives them as scattered pieces ("∑", "J", "j=1"); kept
together they are either cropped from the page as a picture (with the images folder, ADR-0033) or
written as a block that keeps their lines.

Pure: lines and words in, the equations' line ranges out.
"""

import re
from dataclasses import dataclass

from clearmd.backend.services.conversion.pdf.tables import Word

LABEL = re.compile(r"\(\d{1,3}[a-z]?\)")  # (5), (12), (3a)
LABEL_SLACK = 24.0  # points: a number this close to the text's right edge is at the margin
LABEL_GAP_EMS = 2.0  # a number this far from the formula before it is set apart from it
ROW_EMS = 0.35  # words this close vertically are on one row (as tables.ROW_EMS)
GAP_EMS = 5.0  # a blank this tall (in line heights) above or below what is found ends it
MAX_LINES = 16  # an equation's lines at most: more is a page of formulas, not one
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
        start, end = index, index
        # What is found so far, bottom to top, and the number's size (a subscript's is no measure).
        box = [lines[index].bottom, lines[index].top, lines[index].size]
        while start - 1 >= 0 and _joins(lines[start - 1], start - 1, box, labels | taken):
            start -= 1
        while end + 1 < len(lines) and _joins(lines[end + 1], end + 1, box, labels | taken):
            end += 1
        if end - start + 1 <= MAX_LINES:
            found.append(range(start, end + 1))
            taken.update(range(start, end + 1))
    return found


def _label_lines(lines: list[Placed], words: list[Word], right_edge: float) -> set[int]:
    """The lines that hold an equation's number, set apart at the right margin."""
    labels: set[int] = set()
    for word in words:
        if not LABEL.fullmatch(word.text) or word.right < right_edge - LABEL_SLACK:
            continue
        row = [
            other for other in words
            if other is not word and abs(other.bottom - word.bottom) <= ROW_EMS * word.size
            and other.right <= word.left
        ]  # fmt: skip
        before = max((other.right for other in row), default=None)
        if before is not None and word.left - before < LABEL_GAP_EMS * word.size:
            continue  # "… as in (5)": a reference at the end of a line of prose
        for index, line in enumerate(lines):
            holds = line.bottom <= word.bottom + 1 and line.top >= word.top - 1
            if holds and not line.other and line.text.endswith(word.text):
                labels.add(index)
    return labels


def _joins(line: Placed, index: int, box: list[float], stops: set[int]) -> bool:
    """Whether the line is one of the equation's: a line of symbols near what is found (its
    number may stand halfway down it); ``box`` grows with it."""
    if index in stops or line.other or _prose(line.text):
        return False
    reach = GAP_EMS * max(line.size, box[2], 1.0)
    if line.bottom - box[1] > reach or box[0] - line.top > reach:
        return False
    box[0], box[1] = min(box[0], line.bottom), max(box[1], line.top)
    return True


def _prose(text: str) -> bool:
    """A line of sentences: several words, or one that leads into what follows ("as follows:")."""
    stripped = text.strip()
    return (
        len(_WORD.findall(stripped)) >= PROSE_WORDS
        or stripped.endswith(":")
        or _LEADS.match(stripped) is not None
    )
