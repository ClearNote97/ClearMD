"""``table:table`` → a Markdown table; merged cells are simplified, never lost (ADR-0024).

Rows come from header rows, row groups and plain rows, in order. LibreOffice writes runs of empty
cells and rows as one element with a repeat count: an empty run counts once, a filled one at most
``MAX_REPEAT`` times, and a table stops at ``MAX_CELLS`` cells.
"""

from collections.abc import Callable
from dataclasses import dataclass

from clearmd.backend.services.conversion.markdown_out import MARK
from clearmd.backend.services.conversion.odt.xmltree import Element

MAX_REPEAT = 64
MAX_CELLS = 100_000
ROW_CONTAINERS = frozenset({"table:table-header-rows", "table:table-rows", "table:table-row-group"})


@dataclass
class Table:
    markdown: str
    simplified: bool  # merged cells, or more than MAX_CELLS


def _repeat(element: Element, attribute: str, empty: bool) -> int:
    count = element.get(attribute)
    times = int(count) if count.isdigit() else 1
    return 1 if empty else max(1, min(times, MAX_REPEAT))


def _rows(table: Element) -> list[tuple[Element, bool]]:
    """Every row, in order, with whether it is a header row (no recursion)."""
    rows: list[tuple[Element, bool]] = []
    pending: list[tuple[Element, bool]] = [(table, False)]
    while pending:
        element, header = pending.pop()
        children = list(element.elements())
        for child in reversed(children):
            if child.tag == "table:table-row":
                pending.append((child, header))
            elif child.tag in ROW_CONTAINERS:
                pending.append((child, header or child.tag == "table:table-header-rows"))
        if element.tag == "table:table-row":
            rows.append((element, header))
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
    for row, _header in _rows(table):
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
            repeat = _repeat(cell, "table:number-columns-repeated", not text)
            if repeat > 1 and not spend(len(text) * (repeat - 1)):
                repeat, simplified = 1, True
            line.extend([_cell(text)] * repeat)
        rows = _repeat(row, "table:number-rows-repeated", not any(line))
        if rows > 1 and not spend(sum(map(len, line)) * (rows - 1)):
            rows, simplified = 1, True
        cells += len(line) * rows
        if cells > MAX_CELLS:
            simplified = True
            break
        grid.extend([line] * rows)
    grid = [line for line in grid if any(line)]
    if not grid:
        return Table("", simplified)
    width = max(len(line) for line in grid)
    while width > 1 and not any(len(line) >= width and line[width - 1] for line in grid):
        width -= 1  # trailing empty columns
    lines = []
    for index, line in enumerate(grid):
        padded = (line + [""] * width)[:width]
        lines.append(MARK + "| " + " | ".join(padded) + " |")
        if index == 0:
            lines.append(MARK + "|" + "---|" * width)
    return Table("\n".join(lines), simplified)


def _cell(text: str) -> str:
    return " ".join(text.split()).replace("|", "\\|")
