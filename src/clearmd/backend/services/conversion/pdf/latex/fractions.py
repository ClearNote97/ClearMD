"""A bar with what stands above and below it: a fraction, a root, an overline (015)."""

from clearmd.backend.services.conversion.pdf.latex.nodes import Bar, Node
from clearmd.backend.services.conversion.pdf.latex.stacking import axis_of, near_size, stack


def fractions(nodes: list[Node], bars: list[Bar], depth: int) -> list[Node]:
    """Each bar, widest first, with what stands right above and below it: a fraction, an
    overline (a root's, after "√"), an underline; a short bar alone on a row is a minus."""
    from clearmd.backend.services.conversion.pdf.latex.layout import layout

    bars, nodes = _drawn_equals(bars, nodes)
    pending = sorted(bars, key=lambda bar: bar.left - bar.right)  # widest first
    while pending:
        bar = pending.pop(0)
        size = near_size(nodes, bar)
        above = stack(nodes, pending, bar, size, upwards=True)
        below = stack(nodes, pending, bar, size, upwards=False)
        taken_nodes = {id(node) for node in above[0] + below[0]}
        taken_bars = {id(item) for item in above[1] + below[1]}
        if not above[0] and not below[0]:
            if bar.right - bar.left <= 1.2 * size and nodes:
                nodes = [*nodes, Node("-", bar.left, bar.right, bar.at, bar.at, size, bar.at)]
            continue  # a rule the equation does not use
        pending = [item for item in pending if id(item) not in taken_bars]
        rest = [node for node in nodes if id(node) not in taken_nodes]
        if above[0] and below[0]:
            numerator = layout(above[0], above[1], depth + 1)
            denominator = layout(below[0], below[1], depth + 1)
            latex = rf"\frac{{{numerator}}}{{{denominator}}}"
            members = above[0] + below[0]
        elif below[0]:
            inner = layout(below[0], below[1], depth + 1)
            root = _root(rest, bar, size)
            if root is not None:
                rest = [node for node in rest if node is not root]
                latex, members = rf"\sqrt{{{inner}}}", [*below[0], root]
            else:
                latex, members = rf"\overline{{{inner}}}", below[0]
        else:
            inner = layout(above[0], above[1], depth + 1)
            latex, members = rf"\underline{{{inner}}}", above[0]
        built = Node(
            latex,
            min(bar.left, *(node.left for node in members)),
            max(bar.right, *(node.right for node in members)),
            min(bar.at, *(node.bottom for node in members)),
            max(bar.at, *(node.top for node in members)),
            size,
            bar.at if above[0] and below[0] else axis_of(members),
        )
        nodes = [*rest, built]
    return nodes


def _drawn_equals(bars: list[Bar], nodes: list[Node]) -> tuple[list[Bar], list[Node]]:
    """Two short bars of the same ends, one right over the other: an "=" drawn as lines."""
    left_over: list[Bar] = []
    used: set[int] = set()
    ordered = sorted(bars, key=lambda bar: bar.at)
    for index, bar in enumerate(ordered):
        if id(bar) in used:
            continue
        size = near_size(nodes, bar)
        pair = next(
            (other for other in ordered[index + 1 :]
             if id(other) not in used and 0 < other.at - bar.at <= 0.5 * size
             and abs(other.left - bar.left) <= 0.5 and abs(other.right - bar.right) <= 0.5
             and other.right - other.left <= 1.5 * size),
            None,
        )  # fmt: skip
        if pair is None:
            left_over.append(bar)
            continue
        used.update((id(bar), id(pair)))
        middle = (bar.at + pair.at) / 2
        nodes = [*nodes, Node("=", bar.left, bar.right, bar.at, pair.at, size, middle, char="=")]
    return left_over, nodes


def _root(nodes: list[Node], bar: Bar, size: float) -> Node | None:
    """The "√" whose bar this is: right before its start, as high."""
    return next(
        (node for node in nodes
         if node.char == "√" and abs(node.right - bar.left) <= 0.6 * size
         and node.top >= bar.at - 0.4 * size),
        None,
    )  # fmt: skip
