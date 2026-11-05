"""An equation's rows, each piece at its place in half-letter columns (feature 013)."""

from clearmd.backend.services.conversion.pdf.model import Line

ROW_SHARE = 0.35  # of a letter's height: pieces this close vertically are on one row
COLUMN_SHARE = 0.5  # of a letter's height: an equation's columns, about a letter wide
MAX_COLUMN = 200  # an equation's piece starts at most this far right


def laid_out(group: list[Line]) -> tuple[str, ...]:
    """The equation's rows, top first, each piece at its place (in half-letter columns)."""
    left = min(line.left for line in group)
    rows: list[list[Line]] = []
    for line in sorted(group, key=lambda line: (-line.bottom, line.left)):
        if rows and abs(rows[-1][0].bottom - line.bottom) <= ROW_SHARE * max(line.size, 1.0):
            rows[-1].append(line)
        else:
            rows.append([line])
    out = []
    for row in rows:
        text = ""
        for line in sorted(row, key=lambda line: line.left):
            column = round((line.left - left) / max(COLUMN_SHARE * line.size, 1.0))
            text = text.ljust(min(column, MAX_COLUMN)) + (
                " " if text and column <= len(text) else ""
            )
            text += line.text
        out.append(text.rstrip())
    return tuple(out)
