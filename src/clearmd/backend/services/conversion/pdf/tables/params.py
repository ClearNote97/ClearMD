"""Limits two or more of the table modules read."""

MIN_ROWS = 4  # fewer rows: a list, an aligned formula, not a table
MIN_COLUMNS = 3
MAX_COLUMNS = 40  # more columns: no table (scattered words)
MAX_CELL_CHARS = 60  # a cell longer than this is prose: the "table" is a paragraph with gaps
