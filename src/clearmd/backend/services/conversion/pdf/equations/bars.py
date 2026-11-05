"""The lines around each fraction's bar: equations with no number (feature 015)."""

import bisect
import re
from collections.abc import Sequence

from clearmd.backend.services.conversion.pdf.equations.joins import prose, titled
from clearmd.backend.services.conversion.pdf.equations.model import Placed
from clearmd.backend.services.conversion.pdf.equations.params import (
    MAX_LABELS,
    MAX_LINES,
    MAX_ROW_WORDS,
)
from clearmd.backend.services.conversion.pdf.tables import Word

BAR_SHARE = 0.6  # of the text's width: a longer line is a rule, never a fraction's bar
BAR_EMS = 1.6  # a fraction's numerator and denominator stand this close to its bar (in sizes)
SCRIPT_SHARE = 0.9  # text this much smaller under a rule is a footnote
RULED_ROWS = 40.0  # points: the same rule this close above or below is a table's
_RELATION = re.compile(r"[=<>≤≥≠≈≡∈∉⊂⊆∼≃≅∝→⇒⇔]")


def bar_lines(
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
            prose(lines[index].text, True) or titled(lines[index], size) for index in touched
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
