"""The words, tables and rows of a page, and a row's cells (feature 013, ADR-0034)."""

from dataclasses import dataclass

from clearmd.backend.services.conversion.pdf.tables.params import (
    MAX_CELL_CHARS,
    MAX_COLUMNS,
    MIN_COLUMNS,
)

GAP_EMS = 1.0  # a gap this many font sizes wide separates two cells (a space is ~0.25)
ROW_EMS = 0.35  # words this close vertically (in font sizes) are on one row


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
class Row:
    bottom: float
    top: float
    cells: list[tuple[float, float, str]]  # left, right, text


def rows_of(words: list[Word]) -> list[Row]:
    """Words on one baseline (within a fraction of their size), top of the page first, each row's
    words joined into cells where the gap between them is wide."""
    gap = _gap(words)  # once per page
    rows: list[Row] = []
    for word in sorted(words, key=lambda w: (-w.bottom, w.left)):
        row = rows[-1] if rows else None
        if row is not None and abs(row.bottom - word.bottom) <= ROW_EMS * max(word.size, 1.0):
            row.cells.append((word.left, word.right, word.text))
            row.top = max(row.top, word.top)
        else:
            rows.append(Row(word.bottom, word.top, [(word.left, word.right, word.text)]))
    for row in rows:
        row.cells = _cells(sorted(row.cells), gap)
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


def tabular(row: Row) -> bool:
    return MIN_COLUMNS - 1 <= len(row.cells) <= MAX_COLUMNS and all(
        len(text) <= MAX_CELL_CHARS for _, _, text in row.cells
    )
