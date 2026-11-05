"""The pieces in rows by their axis, each small piece on its base (feature 015)."""

from clearmd.backend.services.conversion.pdf.latex.nodes import Node
from clearmd.backend.services.conversion.pdf.latex.params import ROW_EMS, SCRIPT_SIZE
from clearmd.backend.services.conversion.pdf.latex.row_text import row_text
from clearmd.backend.services.conversion.pdf.latex.scripts import base_of


def text_rows(nodes: list[Node], size: float, depth: int) -> list[str]:
    """The pieces in rows (by their axis), each row from the left, scripts on their bases."""
    from clearmd.backend.services.conversion.pdf.latex.layout import layout

    bases = [node for node in nodes if node.size >= SCRIPT_SIZE * size or node.tall]
    small = sorted(
        (node for node in nodes if not (node.size >= SCRIPT_SIZE * size or node.tall)),
        key=lambda node: node.left,
    )
    loose: list[Node] = []
    runs: list[tuple[Node, str, list[Node]]] = []  # base, kind, pieces
    for node in small:
        run = next(
            (run for run in reversed(runs)
             if node.left - run[2][-1].right <= 0.35 * size
             and node.left >= run[2][-1].left
             and abs(node.axis - run[2][-1].axis) <= 0.35 * node.size),
            None,
        )  # fmt: skip
        if run is not None:
            run[2].append(node)
            continue
        attached = base_of(node, bases, size)
        if attached is None:
            loose.append(node)
        else:
            runs.append((attached[0], attached[1], [node]))
    for base, kind, pieces in runs:
        base.reach = max(base.reach, *(piece.right for piece in pieces))
        latex = layout(pieces, [], depth + 1)
        if kind in base.scripts:  # two runs of one kind on a base: written one after the other
            base.scripts[kind] += " " + latex
        else:
            base.scripts[kind] = latex
    placed = bases + loose
    if not placed:
        return []
    rows: list[list[Node]] = []
    for node in sorted(placed, key=lambda node: -node.axis):
        if rows and abs(rows[-1][0].axis - node.axis) <= ROW_EMS * size:
            rows[-1].append(node)
        else:
            rows.append([node])
    return [row_text(sorted(row, key=lambda node: node.left), size) for row in rows]
