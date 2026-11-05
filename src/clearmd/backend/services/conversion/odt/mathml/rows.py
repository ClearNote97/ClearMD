"""Sequences and matrices: stretchy fences around a row become ``\\left`` … ``\\right``."""

from clearmd.backend.services.conversion.odt.mathml.attributes import (
    Unsupported,
    children,
    fence_char,
)
from clearmd.backend.services.conversion.odt.mathml.leaves import join
from clearmd.backend.services.conversion.xmltree import Element


def matrix(table: Element, depth: int) -> str:
    rows = []
    for row in table.elements():
        if row.tag != "math:mtr":
            raise Unsupported(row.tag)
        cells = []
        for cell in row.elements():
            if cell.tag != "math:mtd":
                raise Unsupported(cell.tag)
            cells.append(sequence(children(cell), depth + 1))
        rows.append(" & ".join(cells))
    return "\\begin{matrix}" + " \\\\ ".join(rows) + "\\end{matrix}"


def sequence(elements: list[Element], depth: int) -> str:
    """A sequence; stretchy fences around it become \\left … \\right."""
    from clearmd.backend.services.conversion.odt.mathml.translate import translate

    if len(elements) >= 2:
        opening, closing = fence_char(elements[0]), fence_char(elements[-1])
        if opening is not None and closing is not None:
            inner = sequence(elements[1:-1], depth + 1)
            return join([f"\\left{opening}", inner, f"\\right{closing}"])
        if opening is not None and elements[0].get("form") != "postfix":
            # "left lbrace … right none" (piecewise definitions): an invisible right fence.
            return join([f"\\left{opening}", sequence(elements[1:], depth + 1), "\\right."])
    return join([translate(element, depth + 1) for element in elements])
