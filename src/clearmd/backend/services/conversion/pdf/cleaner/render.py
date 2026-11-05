"""A table, an equation, a picture as the Markdown block ClearMD writes itself (012, 013)."""

from clearmd.backend.services.conversion.markdown_out import (
    MARK,
    escape_math,
    escape_text,
    fence_for,
    link_target,
    math_line,
)
from clearmd.backend.services.conversion.pdf.model import Line


def _cell(text: str) -> str:
    return escape_text(" ".join(text.split())).replace("|", "\\|")


def _table_block(rows: tuple[tuple[str, ...], ...]) -> str:
    header, *body = rows
    lines = [MARK + "| " + " | ".join(_cell(text) for text in header) + " |"]
    lines.append(MARK + "|" + "---|" * len(header))
    lines += [MARK + "| " + " | ".join(_cell(text) for text in row) + " |" for row in body]
    return "\n".join(lines)


def is_block(line: Line) -> bool:
    """A picture, a table or an equation: no text of its own to weigh, repeat or hold."""
    return bool(line.image or line.table or line.equation)


def block_markdown(line: Line) -> str | None:
    if line.latex:  # rebuilt as LaTeX (015): display math, as the TeX converter writes it
        return f"{MARK}$$\n{math_line(escape_math(line.latex))}\n{MARK}$$"
    if line.equation:  # its rows kept, fenced longer than any run of backticks in it
        code = "\n".join(line.equation)
        fence = fence_for(code)
        return f"{MARK}{fence}\n{code}\n{MARK}{fence}"
    if line.table:
        return _table_block(line.table)
    if line.image:
        return f"{MARK}![]({link_target(line.image)})"
    return None
