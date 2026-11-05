"""Where a row's cells fall in the columns, and whether the columns are aligned (013)."""

import bisect

from clearmd.backend.services.conversion.pdf.tables.rows import Row

ALIGN_POINTS = 3.0  # cells of a column start, end or centre this close to one another
ALIGNED_SHARE = 0.7  # of a column's cells: a table's columns are aligned, prose's gaps are not


def placed_in(row: Row, columns: list[tuple[float, float]]) -> list[str]:
    """The row's cells in their columns: a cell spanning several goes to the first it covers (a
    header over two), one between columns to the nearest."""
    out = [""] * len(columns)
    starts = [left for left, _ in columns]
    for left, right, text in row.cells:
        index = bisect.bisect_right(starts, right) - 1  # the last column starting before its end
        first = index
        while first > 0 and columns[first - 1][1] > left:
            first -= 1  # the first one it covers
        if index < 0 or columns[first][1] <= left:  # in none: the nearest by its centre
            centre = (left + right) / 2
            near = [i for i in (index, index + 1) if 0 <= i < len(columns)]
            first = min(near, key=lambda i: abs((columns[i][0] + columns[i][1]) / 2 - centre))
        out[first] = f"{out[first]} {text}".strip()
    return out


def aligned(rows: list[Row], columns: list[tuple[float, float]]) -> bool:
    """Each column's cells share an edge or a centre (left, right or centred text, as tables
    are set); justified prose leaves its gaps anywhere."""
    by_column: list[list[tuple[float, float]]] = [[] for _ in columns]
    starts = [left for left, _ in columns]
    for row in rows:
        for left, right, _ in row.cells:
            index = bisect.bisect_right(starts, right) - 1
            while index >= 0 and columns[index][1] > left:
                by_column[index].append((left, right))
                index -= 1
    for cells in by_column:
        if len(cells) < 2:
            continue
        edges = (
            [left for left, _ in cells],
            [right for _, right in cells],
            [(left + right) / 2 for left, right in cells],
        )
        if max(_densest(values) for values in edges) < ALIGNED_SHARE * len(cells):
            return False
    return True


def _densest(values: list[float]) -> int:
    """The most values within ``ALIGN_POINTS`` of one of them."""
    ordered = sorted(values)
    return max(
        bisect.bisect_right(ordered, value + ALIGN_POINTS)
        - bisect.bisect_left(ordered, value - ALIGN_POINTS)
        for value in ordered
    )
