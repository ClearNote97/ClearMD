"""The lines a table found on the page replaces, where its first line stood (feature 013)."""

from clearmd.backend.services.conversion.pdf.lattice import Rule, find_lattices
from clearmd.backend.services.conversion.pdf.model import CLOCKWISE, COUNTERCLOCKWISE, UPRIGHT, Line
from clearmd.backend.services.conversion.pdf.tables import Table, Word, find_tables

ROW_SLACK = 1.0  # points: a line within a table's top and bottom is one of its rows


def tabled(lines: list[Line], words: dict[int, list[Word]], rules: list[Rule]) -> list[Line]:
    """The lines a table found on the page covers give way to it, where its first one stood:
    ruled tables first (their words then taken), then the others by their aligned words. A table
    set sideways is found in its own frame (the page turned upright), then placed back."""
    for table, taken in find_lattices(rules, words[UPRIGHT]):
        box = (table.bottom, table.top, table.left, table.right)
        lines = replaced(lines, table, UPRIGHT, box)
        gone = {id(word) for word in taken}
        words = {**words, UPRIGHT: [word for word in words[UPRIGHT] if id(word) not in gone]}
    for turn, turned in words.items():
        for table in find_tables(turned):
            # The table's box on the page: (bottom, top, left, right).
            box = {
                UPRIGHT: (table.bottom, table.top, table.left, table.right),
                CLOCKWISE: (-table.right, -table.left, table.bottom, table.top),
                COUNTERCLOCKWISE: (table.left, table.right, -table.top, -table.bottom),
            }[turn]
            lines = replaced(lines, table, turn, box)
    return lines


def replaced(
    lines: list[Line], table: Table, turn: int, box: tuple[float, float, float, float]
) -> list[Line]:
    low, high, left, right = box
    inside = [
        i for i, line in enumerate(lines)
        if line.turn == turn and not (line.table or line.image or line.equation)
        and line.bottom >= low - ROW_SLACK and line.top <= high + ROW_SLACK
        and line.left >= left - ROW_SLACK and line.right <= right + ROW_SLACK
    ]  # fmt: skip
    if inside:
        block = Line("", 0.0, False, high, low, table=table.rows, left=left, right=right)
        lines = [line for i, line in enumerate(lines) if i not in set(inside)]
        lines.insert(inside[0], block)
    return lines
