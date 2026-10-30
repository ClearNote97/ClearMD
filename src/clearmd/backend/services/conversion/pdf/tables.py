"""Tables in a PDF page, found from where its words stand (feature 013, ADR-0034).

After Camelot's "stream" method (Vinayak Mehta and contributors, MIT; https://camelot-py.readthedocs.io):
a table is a run of rows whose words leave the same wide gaps, its columns are where those gaps
fall. Camelot reads pdfminer's text; ClearMD reads PDFium's own character boxes, and needs neither
OpenCV nor Ghostscript.

Pure: words in, tables out. Every cell is document text, escaped by the writer (ADR-0023).
"""

import re
from collections import Counter
from dataclasses import dataclass

GAP_EMS = 1.0  # a gap this many font sizes wide separates two cells (a space is ~0.25)
ROW_EMS = 0.35  # words this close vertically (in font sizes) are on one row
MIN_ROWS = 4  # fewer rows: a list, an aligned formula, not a table
MIN_COLUMNS = 3
ROW_GAP_LINES = 2.5  # a blank this many rows tall ends a table
MAX_GAP_ROWS = 6  # one-cell rows (a cell's wrapped text) a table goes on after
MAX_CELL_CHARS = 60  # a cell longer than this is prose: the "table" is a paragraph with gaps
ALIGN_POINTS = 3.0  # cells of a column start, end or centre this close to one another
ALIGNED_SHARE = 0.7  # of a column's cells: a table's columns are aligned, prose's gaps are not
CONTENT_SHARE = 0.6  # of its cells hold a number or a word (three letters): not a formula


@dataclass(frozen=True)
class Word:
    text: str
    left: float
    right: float
    bottom: float
    top: float
    size: float


@dataclass(frozen=True)
class Table:
    top: float
    bottom: float
    left: float
    right: float
    rows: tuple[tuple[str, ...], ...]  # the first row is the header


@dataclass
class _Row:
    bottom: float
    top: float
    cells: list[tuple[float, float, str]]  # left, right, text


def _rows(words: list[Word]) -> list[_Row]:
    """Words on one baseline (within a fraction of their size), top of the page first, each row's
    words joined into cells where the gap between them is wide."""
    rows: list[_Row] = []
    for word in sorted(words, key=lambda w: (-w.bottom, w.left)):
        row = rows[-1] if rows else None
        if row is not None and abs(row.bottom - word.bottom) <= ROW_EMS * max(word.size, 1.0):
            row.cells.append((word.left, word.right, word.text))
            row.top = max(row.top, word.top)
        else:
            rows.append(_Row(word.bottom, word.top, [(word.left, word.right, word.text)]))
    for row in rows:
        row.cells = _cells(sorted(row.cells), _gap(words))
    return rows


def _gap(words: list[Word]) -> float:
    sizes = sorted(word.size for word in words) or [10.0]
    return GAP_EMS * sizes[len(sizes) // 2]


def _cells(pieces: list[tuple[float, float, str]], gap: float) -> list[tuple[float, float, str]]:
    cells: list[tuple[float, float, str]] = []
    for left, right, text in pieces:
        if cells and left - cells[-1][1] < gap:
            last = cells[-1]
            cells[-1] = (last[0], max(last[1], right), f"{last[2]} {text}")
        else:
            cells.append((left, right, text))
    return cells


def _tabular(row: _Row) -> bool:
    return len(row.cells) >= MIN_COLUMNS - 1 and all(
        len(text) <= MAX_CELL_CHARS for _, _, text in row.cells
    )


def _columns(rows: list[_Row]) -> tuple[list[tuple[float, float]], list[_Row]]:
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
                if not any(left < b and right > a for a, b in columns)
            ]  # fmt: skip
            columns = _merged(columns + new)
    return columns, seed


def _merged(spans: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Spans merged where they overlap; a span that bridges two others apart ("Municipal 2012–2013"
    over the court's and the period's columns) joins none: it is placed afterwards."""
    columns: list[list[float]] = []
    kept = [span for span in spans if not _bridge(span, spans)]
    for left, right in sorted(kept or spans):
        if columns and left <= columns[-1][1]:
            columns[-1][1] = max(columns[-1][1], right)
        else:
            columns.append([left, right])
    return [(left, right) for left, right in columns]


def _bridge(span: tuple[float, float], spans: list[tuple[float, float]]) -> bool:
    under = [(a, b) for a, b in spans if (a, b) != span and a < span[1] and b > span[0]]
    return any(b1 <= a2 for _, b1 in under for a2, _ in under)


def _placed(row: _Row, columns: list[tuple[float, float]]) -> list[str]:
    """The row's cells in their columns: a cell spanning several goes to the first it covers (a
    header over two), one between columns to the nearest."""
    out = [""] * len(columns)
    for left, right, text in row.cells:
        hit = [i for i, (a, b) in enumerate(columns) if left < b and right > a]
        centre = (left + right) / 2
        index = hit[0] if hit else min(
            range(len(columns)), key=lambda i: abs((columns[i][0] + columns[i][1]) / 2 - centre)
        )  # fmt: skip
        out[index] = f"{out[index]} {text}".strip()
    return out


def _aligned(rows: list[_Row], columns: list[tuple[float, float]]) -> bool:
    """Each column's cells share an edge or a centre (left, right or centred text, as tables
    are set); justified prose leaves its gaps anywhere."""
    for left_edge, right_edge in columns:
        cells = [
            (left, right) for row in rows for left, right, _ in row.cells
            if left < right_edge and right > left_edge
        ]  # fmt: skip
        if len(cells) < 2:
            continue
        best = 0
        edges = (
            [left for left, _ in cells],
            [right for _, right in cells],
            [(left + right) / 2 for left, right in cells],
        )
        for values in edges:
            best = max(
                best,
                max(sum(1 for v in values if abs(v - anchor) <= ALIGN_POINTS) for anchor in values),
            )
        if best < ALIGNED_SHARE * len(cells):
            return False
    return True


def find_tables(words: list[Word]) -> list[Table]:
    """The page's tables, top first: runs of at least ``MIN_ROWS`` tabular rows whose cells fall
    into at least ``MIN_COLUMNS`` columns."""
    rows = _rows(words)
    tables: list[Table] = []
    run: list[_Row] = []
    for index, row in enumerate([*rows, None]):
        apart = row is not None and bool(run) and _apart(run[-1], row)
        if (
            row is not None
            and not apart
            and (_tabular(row) or _within(run, row, rows[index + 1 :]))
        ):
            run.append(row)
            continue
        table = _table(run)
        if table is not None:
            tables.append(table)
        run = [row] if row is not None and apart and _tabular(row) else []
    return tables


def _apart(above: _Row, row: _Row) -> bool:
    """A blank of several lines between two rows: two tables, or a table and the text after."""
    return above.bottom - row.top > ROW_GAP_LINES * max(above.top - above.bottom, 1.0)


def _within(run: list[_Row], row: _Row, after: list[_Row]) -> bool:
    """Short one-cell rows between two of a table's belong to it: a group's note under its name
    ("(33 districts, 165 Obs.)"), a cell's text wrapped over several lines."""
    return (
        bool(run)
        and len(row.cells) == 1
        and len(row.cells[0][2]) <= MAX_CELL_CHARS
        and any(_tabular(next_row) for next_row in after[:MAX_GAP_ROWS])
    )


_NUMBER = re.compile(r"[−–-]?\d[\d.,]*%?")  # 3, 0.871, 12,5, −0.037, 45%


def _letters(cell: str) -> int:
    return sum(char.isalnum() for char in cell)


def _table(run: list[_Row]) -> Table | None:
    if len(run) < MIN_ROWS:
        return None
    columns, seed = _columns(run)
    if len(seed) < MIN_ROWS - 1 or len(columns) < MIN_COLUMNS or not _aligned(seed, columns):
        return None
    matched = [_placed(row, columns) for row in run]
    filled = [cell for cells in matched for cell in cells if cell]
    worded = sum(1 for cell in filled if _NUMBER.fullmatch(cell) or _letters(cell) >= 3)
    if worded < CONTENT_SHARE * len(filled):  # "=", "t+1", "(x": an aligned formula
        return None
    return Table(
        top=max(row.top for row in run),
        bottom=min(row.bottom for row in run),
        left=columns[0][0],
        right=columns[-1][1],
        rows=tuple(tuple(cells) for cells in matched),
    )
