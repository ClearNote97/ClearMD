"""``table:table`` → a Markdown table; merged cells are simplified, never lost (ADR-0024).

Rows come from header rows, row groups and plain rows, in order. LibreOffice writes runs of empty
cells and rows as one element with a repeat count: an empty run counts once, a filled one at most
``MAX_REPEAT`` times, and a table stops at ``MAX_CELLS`` cells.
"""

from collections.abc import Callable
from dataclasses import dataclass

from clearmd.backend.services.conversion.markdown_out import MARK
from clearmd.backend.services.conversion.odt.xmltree import Element, int_attribute

MAX_REPEAT = 64
MAX_CELLS = 100_000
ROW_CONTAINERS = frozenset({"table:table-header-rows", "table:table-rows", "table:table-row-group"})


@dataclass
class Table:
    markdown: str
    simplified: bool  # merged cells, or more than MAX_CELLS


def _repeat(element: Element, attribute: str) -> int:
    return max(1, min(int_attribute(element.get(attribute), 1), MAX_REPEAT))


def _rows(table: Element) -> list[Element]:
    """Every row, in order, header rows first as written (no recursion)."""
    rows: list[Element] = []
    pending: list[Element] = [table]
    while pending:
        element = pending.pop()
        for child in reversed(list(element.elements())):
            if child.tag == "table:table-row" or child.tag in ROW_CONTAINERS:
                pending.append(child)
        if element.tag == "table:table-row":
            rows.append(element)
    return rows


def table_to_markdown(
    table: Element,
    render_cell: Callable[[Element], str],
    spend: Callable[[int], bool] = lambda _: True,
) -> Table:
    """``spend`` charges the characters that repeats add to the document's growth budget."""
    simplified = False
    grid: list[list[str]] = []  # header rows come first: the first row is the header
    cells = 0
    for row in _rows(table):
        line: list[str] = []
        for cell in row.elements():
            if cell.tag not in {"table:table-cell", "table:covered-table-cell"}:
                continue
            covered = cell.tag == "table:covered-table-cell"
            text = "" if covered else render_cell(cell)
            if covered or cell.get("table:number-columns-spanned") not in {"", "1"}:
                simplified = True
            if cell.get("table:number-rows-spanned") not in {"", "1"}:
                simplified = True
            # An empty run keeps the columns after it in place; trailing empty columns go below.
            repeat = _repeat(cell, "table:number-columns-repeated")
            if repeat > 1 and not spend(len(text) * (repeat - 1)):
                repeat, simplified = 1, True
            line.extend([_cell(text)] * repeat)
        rows = _repeat(row, "table:number-rows-repeated") if any(line) else 1
        if rows > 1 and not spend(sum(map(len, line)) * (rows - 1)):
            rows, simplified = 1, True
        cells += len(line) * rows
        if cells > MAX_CELLS:
            simplified = True
            break
        grid.extend([line] * rows)
    # Trailing empty cells go, in one pass (a repeated row is the same list: trimmed once).
    trimmed: dict[int, list[str]] = {}
    for line in grid:
        if id(line) not in trimmed:
            end = len(line)
            while end and not line[end - 1]:
                end -= 1
            trimmed[id(line)] = line[:end]
    grid = [trimmed[id(line)] for line in grid if trimmed[id(line)]]
    if not grid:
        return Table("", simplified)
    width = max(len(line) for line in grid)
    # The header row and the rule set the columns; a shorter row is completed by the viewer,
    # so the padding is written only while the budget pays for it, and the header only if so.
    if not spend(8 * width):
        grid = [[text for text in line if text] for line in grid]  # every text, fewer columns
        width, simplified = max(len(line) for line in grid), True
    padding = sum(3 * (width - len(line)) for line in grid[1:])
    padded = spend(padding)
    lines = []
    for index, line in enumerate(grid):
        if index == 0 or padded:
            line = line + [""] * (width - len(line))
        lines.append(MARK + "| " + " | ".join(line) + " |")
        if index == 0:
            lines.append(MARK + "|" + "---|" * width)
    return Table("\n".join(lines), simplified)


def _cell(text: str) -> str:
    return " ".join(text.split()).replace("|", "\\|")
