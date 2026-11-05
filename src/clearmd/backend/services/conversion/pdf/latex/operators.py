"""A sum's limits: the smaller pieces right above and below it (feature 015)."""

from clearmd.backend.services.conversion.pdf.latex.nodes import Node
from clearmd.backend.services.conversion.pdf.latex.params import SCRIPT_SIZE
from clearmd.backend.services.conversion.pdf.latex.symbols import BIG_OPERATORS


def limits(nodes: list[Node], size: float, depth: int) -> list[Node]:
    """A sum's limits: the smaller pieces right above and below it, within its width."""
    from clearmd.backend.services.conversion.pdf.latex.layout import layout

    operators = [node for node in nodes if node.char in BIG_OPERATORS]
    if not operators:
        return nodes
    taken: set[int] = set()
    for operator in operators:
        operator.tall = True
        reach = max(operator.right - operator.left, size)
        for place, upwards in (("over", True), ("under", False)):
            found = [
                node for node in nodes
                if id(node) not in taken and node is not operator
                and node.size < SCRIPT_SIZE * size
                and abs((node.left + node.right) / 2 - (operator.left + operator.right) / 2)
                <= reach
                and (node.bottom >= operator.top - 0.25 * size if upwards
                     else node.top <= operator.bottom + 0.25 * size)
                and (node.bottom - operator.top if upwards else operator.bottom - node.top)
                <= 1.2 * size
            ]  # fmt: skip
            found = _row_of(found, operator, upwards)
            if found:
                operator.scripts[place] = layout(found, [], depth + 1)
                taken.update(id(node) for node in found)
    return [node for node in nodes if id(node) not in taken]


def _row_of(found: list[Node], operator: Node, upwards: bool) -> list[Node]:
    """The row of limits next to the operator (the nearest one), all of it."""
    if not found:
        return []
    nearest = min(found, key=lambda node: abs(node.middle - operator.middle))
    return [node for node in found if abs(node.axis - nearest.axis) <= 0.5 * nearest.size]
