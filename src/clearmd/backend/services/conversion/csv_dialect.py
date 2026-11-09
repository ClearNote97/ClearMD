"""A CSV's separator, found from its first lines (audit 2026-11-08, B1-03).

Excel in Spanish (and most of Europe and Latin America) saves "CSV" with semicolons; markitdown
reads commas only and would make one column. A file whose lines split evenly on ``;``, a tab or
``|``, and not on commas, is rewritten with commas before markitdown reads it (decoded once,
as every plain text is, by the shared decoder: audit 2026-11-09, B1-01).
"""

import csv
import io
from collections import Counter

SEPARATORS = (",", ";", "\t", "|")
SAMPLE_LINES = 50


def _score(lines: list[str], separator: str) -> tuple[float, int]:
    """How evenly the lines split: the share of rows with the usual width, and that width."""
    widths = [len(row) for row in csv.reader(lines, delimiter=separator) if row]
    if not widths:
        return 0.0, 1
    width, count = Counter(widths).most_common(1)[0]
    return (count / len(widths) if width > 1 else 0.0), width


def separator(text: str) -> str:
    """The separator that splits the first lines into the same number of columns; a comma when
    none does better (a one-column file stays as it is)."""
    lines = [line for line in text.splitlines()[:SAMPLE_LINES] if line.strip()]
    best, best_score = ",", _score(lines, ",")
    for candidate in SEPARATORS[1:]:
        score = _score(lines, candidate)
        if score > best_score:
            best, best_score = candidate, score
    return best


def with_commas(text: str) -> str:
    """``text`` rewritten with commas when it uses another separator; as it is otherwise."""
    found = separator(text)
    if found == ",":
        return text
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerows(csv.reader(io.StringIO(text, newline=""), delimiter=found))
    return out.getvalue()
