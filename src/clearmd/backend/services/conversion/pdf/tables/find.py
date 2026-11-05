"""The page's tables: runs of tabular rows (feature 013, ADR-0034)."""

from clearmd.backend.services.conversion.pdf.tables.build import table_of
from clearmd.backend.services.conversion.pdf.tables.params import MAX_CELL_CHARS
from clearmd.backend.services.conversion.pdf.tables.rows import Row, Table, Word, rows_of, tabular

MAX_ROWS = 400  # a table's rows at most: a longer run is cut into tables of this many
ROW_GAP_LINES = 2.5  # a blank this many rows tall ends a table
MAX_GAP_ROWS = 6  # one-cell rows (a cell's wrapped text) a table goes on after


def find_tables(words: list[Word]) -> list[Table]:
    """The page's tables, top first: runs of at least ``MIN_ROWS`` tabular rows whose cells fall
    into at least ``MIN_COLUMNS`` columns."""
    rows = rows_of(words)
    tables: list[Table] = []
    run: list[Row] = []
    for index, row in enumerate([*rows, None]):
        apart = row is not None and bool(run) and (_apart(run[-1], row) or len(run) >= MAX_ROWS)
        if row is not None and not apart and (tabular(row) or _within(run, row, rows, index)):
            run.append(row)
            continue
        table = table_of(run)
        if table is not None:
            tables.append(table)
        run = [row] if row is not None and apart and tabular(row) else []
    return tables


def _apart(above: Row, row: Row) -> bool:
    """A blank of several lines between two rows: two tables, or a table and the text after."""
    return above.bottom - row.top > ROW_GAP_LINES * max(above.top - above.bottom, 1.0)


def _within(run: list[Row], row: Row, rows: list[Row], index: int) -> bool:
    """Short one-cell rows between two of a table's belong to it: a group's note under its name
    ("(33 districts, 165 Obs.)"), a cell's text wrapped over several lines."""
    return (
        bool(run)
        and len(row.cells) == 1
        and len(row.cells[0][2]) <= MAX_CELL_CHARS
        and any(tabular(after) for after in rows[index + 1 : index + 1 + MAX_GAP_ROWS])
    )
