"""A run of rows made a table, or refused: formulas, lists and prose are not (013)."""

import re

from clearmd.backend.services.conversion.pdf.tables.columns import columns_of
from clearmd.backend.services.conversion.pdf.tables.grid import aligned, placed_in
from clearmd.backend.services.conversion.pdf.tables.params import MAX_COLUMNS, MIN_COLUMNS, MIN_ROWS
from clearmd.backend.services.conversion.pdf.tables.rows import Row, Table

CONTENT_SHARE = 0.6  # of its cells hold a number or a word (three letters): not a formula
PROSE_SHARE = 0.6  # of a column's cells starting in lowercase, several words each: prose
PROSE_WORDS = 4
MARKER_SHARE = 0.8  # of the first column's cells that are list markers: a list, not a table
_MARKER = re.compile(r"[•·▪◦‣∙*–-]|\(?\[?\d{1,3}[.)\]]?|\(?[a-zA-Z][.)]")
_NUMBER = re.compile(r"[−–-]?\d[\d.,]*%?")  # 3, 0.871, 12,5, −0.037, 45%


def _letters(cell: str) -> int:
    return sum(char.isalnum() for char in cell)


def table_of(run: list[Row]) -> Table | None:
    if len(run) < MIN_ROWS:
        return None
    columns, seed = columns_of(run)
    if len(seed) < MIN_ROWS - 1 or not MIN_COLUMNS <= len(columns) <= MAX_COLUMNS:
        return None
    if not aligned(seed, columns):
        return None
    matched = [placed_in(row, columns) for row in run]
    filled = [cell for cells in matched for cell in cells if cell]
    worded = sum(1 for cell in filled if _NUMBER.fullmatch(cell) or _letters(cell) >= 3)
    if worded < CONTENT_SHARE * len(filled):  # "=", "t+1", "(x": an aligned formula
        return None
    if _a_list(matched) or any(_prose(matched, column) for column in range(len(columns))):
        return None
    matched = joined_continuations(matched)
    return Table(
        top=max(row.top for row in run),
        bottom=min(row.bottom for row in run),
        left=min(left for row in run for left, _, _ in row.cells),
        right=max(right for row in run for _, right, _ in row.cells),
        rows=tuple(tuple(cells) for cells in matched),
    )


def _a_list(rows: list[list[str]]) -> bool:
    """A list set with tabs ("•  Name   Ana", "[1]  Author  Title"): its first column is markers."""
    first = [cells[0] for cells in rows if cells[0]]
    return bool(first) and sum(1 for c in first if _MARKER.fullmatch(c)) >= MARKER_SHARE * len(rows)


def _prose(rows: list[list[str]], column: int) -> bool:
    """A column of running text (a page's other column beside a table): its lines go on from one
    another, most starting in lowercase, several words each."""
    cells = [cells[column] for cells in rows if cells[column]]
    running = [c for c in cells if c[0].islower() and len(c.split()) >= PROSE_WORDS]
    return len(cells) >= MIN_ROWS and len(running) >= PROSE_SHARE * len(cells)


def joined_continuations(rows: list[list[str]]) -> list[list[str]]:
    """A cell written over several lines stays one cell (ADR-0034; audit 2026-11-09, B3-01): a
    line whose first cell is empty and that fills at most half the columns goes on the row above,
    each piece after its column's text. A row with most cells filled is a row of its own (a
    grouped first column)."""
    joined: list[list[str]] = []
    for cells in rows:
        filled = sum(1 for cell in cells if cell)
        if joined and not cells[0] and 0 < filled <= max(1, len(cells) // 2):
            above = joined[-1]
            for index, cell in enumerate(cells):
                if cell:
                    above[index] = f"{above[index]} {cell}".strip()
            continue
        joined.append(list(cells))
    return joined
