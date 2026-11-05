"""A table's columns, as Camelot's stream method finds them (feature 013)."""

import bisect
from collections import Counter

from clearmd.backend.services.conversion.pdf.tables.params import MIN_COLUMNS
from clearmd.backend.services.conversion.pdf.tables.rows import Row

BRIDGE_LOOKS = 64  # spans looked at, each way, to tell whether one bridges two others


def columns_of(rows: list[Row]) -> tuple[list[tuple[float, float]], list[Row]]:
    """The table's columns, as Camelot's stream finds them: the cells of the rows with the commonest
    number of cells, merged where they overlap; then a cell of a fuller row that falls in none
    opens one ("Circuit courts", once per group). A header spanning several ("Type of court")
    sets none. Also the rows that set them."""
    counts = Counter(len(row.cells) for row in rows if len(row.cells) >= MIN_COLUMNS)
    if not counts:
        return [], []
    commonest = max(counts, key=lambda count: (counts[count], count))
    seed = [row for row in rows if len(row.cells) == commonest]
    columns = _merged([(left, right) for row in seed for left, right, _ in row.cells])
    for row in rows:
        if len(row.cells) > commonest:
            new = [
                (left, right) for left, right, _ in row.cells
                if not _overlaps_any(left, right, columns)
            ]  # fmt: skip
            if new:
                columns = _merged(columns + new)
    return columns, seed


def _overlaps_any(left: float, right: float, columns: list[tuple[float, float]]) -> bool:
    """Whether the span overlaps one of the (sorted, disjoint) columns."""
    index = bisect.bisect_left(columns, (right,))  # the columns starting before its right end
    return index > 0 and columns[index - 1][1] > left


def _merged(spans: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Spans merged where they overlap; a span that bridges two others apart ("Municipal 2012–2013"
    over the court's and the period's columns) joins none: it is placed afterwards."""
    ordered = sorted(spans)
    bridges = _bridges(ordered)
    kept = [span for index, span in enumerate(ordered) if index not in bridges]
    columns: list[list[float]] = []
    for left, right in kept or ordered:
        if columns and left <= columns[-1][1]:
            columns[-1][1] = max(columns[-1][1], right)
        else:
            columns.append([left, right])
    return [(left, right) for left, right in columns]


def _bridges(spans: list[tuple[float, float]]) -> set[int]:
    """The spans (sorted by start) that overlap two others which do not overlap each other: the
    other overlapping span that ends first ends before the one that starts last begins. Each
    side looked up by bisection, a bounded number of neighbours each."""
    starts = [left for left, _ in spans]
    by_end = sorted(range(len(spans)), key=lambda i: spans[i][1])
    ends = [spans[i][1] for i in by_end]
    found: set[int] = set()
    for index, (left, right) in enumerate(spans):
        last_start = None  # the overlapping span that starts last: starts before ``right``
        for other in range(bisect.bisect_left(starts, right) - 1, -1, -1)[:BRIDGE_LOOKS]:
            if other != index and spans[other][1] > left:
                last_start = spans[other][0]
                break
        first_end = None  # the overlapping span that ends first: ends after ``left``
        for position in range(bisect.bisect_right(ends, left), len(ends))[:BRIDGE_LOOKS]:
            other = by_end[position]
            if other != index and spans[other][0] < right:
                first_end = spans[other][1]
                break
        if last_start is not None and first_end is not None and first_end <= last_start:
            found.add(index)
    return found
