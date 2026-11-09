"""A CSV's separator, found from its first lines (audit 2026-11-08, B1-03).

Excel in Spanish (and most of Europe and Latin America) saves "CSV" with semicolons; markitdown
reads commas only and would make one column. A file whose lines split evenly on ``;``, a tab or
``|``, and not on commas, is rewritten with commas (UTF-8) before markitdown reads it.
"""

import csv
import io
from collections import Counter

from charset_normalizer import from_bytes

SEPARATORS = (",", ";", "\t", "|")
SAMPLE_LINES = 50


def _decoded(data: bytes) -> str:
    """As markitdown decodes it: the most likely encoding, BOM removed."""
    best = from_bytes(data).best()
    text = str(best) if best is not None else data.decode("utf-8", errors="ignore")
    return text.lstrip("﻿")


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


def with_commas(data: bytes) -> bytes | None:
    """``data`` rewritten with commas, or ``None`` when it already uses them."""
    text = _decoded(data)
    found = separator(text)
    if found == ",":
        return None
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerows(csv.reader(io.StringIO(text, newline=""), delimiter=found))
    return out.getvalue().encode("utf-8")
