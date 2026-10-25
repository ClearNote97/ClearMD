r"""``tabular`` → a Markdown table, or ``None`` when Markdown cannot show it faithfully."""

from collections.abc import Callable
from typing import Any

from pylatexenc.latexwalker import LatexMacroNode, LatexSpecialsNode

MERGED_CELLS = frozenset({"multicolumn", "multirow"})
RULES = frozenset({"hline", "toprule", "midrule", "bottomrule", "cline", "hhline", "cmidrule"})
ROW_ENDS = frozenset({"\\", "tabularnewline"})


def _descendants(nodes: list[Any]) -> list[Any]:
    found = []
    for node in nodes:
        if node is None:
            continue
        found.append(node)
        found.extend(_descendants(getattr(node, "nodelist", None) or []))
        arguments = getattr(getattr(node, "nodeargd", None), "argnlist", None) or []
        found.extend(_descendants([argument for argument in arguments if argument is not None]))
    return found


def has_merged_cells(environment: Any) -> bool:
    return any(
        isinstance(node, LatexMacroNode) and node.macroname in MERGED_CELLS
        for node in _descendants(environment.nodelist or [])
    )


def tabular_to_markdown(environment: Any, render_cell: Callable[[list[Any]], str]) -> str | None:
    """The rows and cells of a tabular; ``None`` for merged cells (they need LaTeX)."""
    if has_merged_cells(environment):
        return None
    rows: list[list[str]] = []
    cell: list[Any] = []
    row: list[str] = []
    for node in environment.nodelist or []:
        if isinstance(node, LatexMacroNode) and node.macroname in RULES:
            continue
        if isinstance(node, LatexSpecialsNode) and node.specials_chars == "&":
            row.append(_cell(render_cell(cell)))
            cell = []
        elif isinstance(node, LatexMacroNode) and node.macroname in ROW_ENDS:
            row.append(_cell(render_cell(cell)))
            rows.append(row)
            cell, row = [], []
        else:
            cell.append(node)
    last = _cell(render_cell(cell))
    if row or last:
        rows.append([*row, last])
    rows = [r for r in rows if any(r)]
    if not rows:
        return None
    width = max(len(r) for r in rows)
    lines = []
    for index, r in enumerate(rows):
        cells = r + [""] * (width - len(r))
        lines.append("| " + " | ".join(cells) + " |")
        if index == 0:
            lines.append("|" + "---|" * width)
    return "\n".join(lines)


def _cell(text: str) -> str:
    return " ".join(text.split()).replace("|", "\\|")
