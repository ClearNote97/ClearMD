"""Tables: rows of cells as a Markdown table, within ``MAX_CELLS`` and the growth budget.

It stands alone because ``MAX_CELLS`` lives where it is read (tests patch it here).
"""

from clearmd.backend.services.conversion.html.writer.runs import inline_of
from clearmd.backend.services.conversion.html.writer.shapes import one_line, row_cells, table_rows
from clearmd.backend.services.conversion.html.writer.state import Writer
from clearmd.backend.services.conversion.markdown_out import MARK, block, escape_text
from clearmd.backend.services.conversion.xmltree import Element

MAX_CELLS = 100_000


def table_block(w: Writer, element: Element) -> str:
    grid: list[list[str]] = []
    plain: list[str] = []  # the cells' text, for a table the budget cannot pay for
    overflow: list[str] = []  # the text of the rows past MAX_CELLS
    cells = 0
    for row in table_rows(element):
        texts = [" ".join(cell.text().split()) for cell in row_cells(row)]
        if cells + len(texts) > MAX_CELLS:
            if not overflow:
                w.state.note_unknown("table")  # its text follows the table, as a paragraph
            overflow.append(" ".join(text for text in texts if text))
            cells += len(texts)
            continue
        line = [
            one_line(inline_of(w, cell.children)).replace("|", "\\|") for cell in row_cells(row)
        ]
        plain.extend(texts)
        cells += len(line)
        while line and not line[-1]:
            line.pop()
        if line:
            grid.append(line)
    after = block(escape_text(" ".join(t for t in overflow if t))) if overflow else ""
    if not grid:
        return after
    width = max(len(line) for line in grid)
    caption = ""
    if len(grid) > 1 and len(grid[0]) == 1 and width > 1:  # a caption, not the header
        caption = block(grid.pop(0)[0])
    if not w.state.spend(8 * width + sum(3 * (width - len(line)) for line in grid)):
        return block(escape_text(" ".join(text for text in plain if text))) + after
    rows = [MARK + "| " + " | ".join(line + [""] * (width - len(line))) + " |" for line in grid]
    rows.insert(1, MARK + "|" + "---|" * width)
    return caption + block("\n".join(rows)) + after
