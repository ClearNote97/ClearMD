"""The lines that hold an equation's number, set apart at the right margin (013)."""

import bisect
import re

from clearmd.backend.services.conversion.pdf.equations.model import Placed
from clearmd.backend.services.conversion.pdf.equations.params import MAX_LABELS, MAX_ROW_WORDS
from clearmd.backend.services.conversion.pdf.tables import Word

LABEL = re.compile(r"\(\d{1,3}[a-z]?\)")  # (5), (12), (3a)
LABEL_SLACK = 24.0  # points: a number this close to the text's right edge is at the margin
LABEL_GAP_EMS = 2.0  # a number this far from the formula before it is set apart from it
ROW_EMS = 0.35  # words this close vertically are on one row (as tables.ROW_EMS)
LINE_REACH = 40  # points: a line holding a number starts at most this far below it


def label_lines(lines: list[Placed], words: list[Word], right_edge: float) -> dict[int, float]:
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
