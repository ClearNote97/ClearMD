"""Tall brackets with what they hold, written with LaTeX left and right (feature 015)."""

from clearmd.backend.services.conversion.pdf.latex.nodes import Node
from clearmd.backend.services.conversion.pdf.latex.symbols import (
    CLOSERS,
    DELIMITERS,
    OPENERS,
    SYMMETRIC,
)

TALL = 1.5  # a bracket taller than this many times the text's size spans what it holds
SAME_HEIGHT = 0.6  # of the shorter: two brackets that overlap this much are a pair


def brackets(nodes: list[Node], size: float, depth: int) -> list[Node]:
    """Tall brackets with what they hold: ``\\left[ … \\right]``, innermost first. Bars
    ("|…|", "‖…‖") pair from the left with the next one alike; a tall brace with no closing one
    holds the rest of its height (a system: ``\\left\\{ … \\right.``)."""
    for node in nodes:
        if node.char in OPENERS or node.char in CLOSERS:
            node.tall = node.top - node.bottom > TALL * size
    bars = sorted((n for n in nodes if n.tall and n.char in SYMMETRIC), key=lambda n: n.left)
    while bars:
        opener = bars.pop(0)
        closer = next((n for n in bars if n.char == opener.char and _level(opener, n)), None)
        if closer is None:
            opener.tall = False
            continue
        bars.remove(closer)
        nodes = _enclosed(nodes, opener, closer, size, depth)
    openers = sorted(
        (node for node in nodes if node.tall and node.char in OPENERS),
        key=lambda node: -node.left,
    )
    for opener in openers:
        if opener not in nodes:
            continue
        closer = next(
            (node for node in sorted(nodes, key=lambda n: n.left)
             if node is not opener and node.tall and node.char in CLOSERS
             and node.char not in SYMMETRIC
             and node.left >= opener.right - 0.1 * size and _level(opener, node)),
            None,
        )  # fmt: skip
        if closer is None and opener.char != "{":
            opener.tall = False  # an unmatched one is written as a plain bracket
            continue
        nodes = _enclosed(nodes, opener, closer, size, depth)
    for node in nodes:
        if node.char in CLOSERS and node.tall:
            node.tall = False  # a closing one with no opening one: plain
    return nodes


def _enclosed(
    nodes: list[Node], opener: Node, closer: Node | None, size: float, depth: int
) -> list[Node]:
    """The pieces between two tall brackets (or after a brace), as one piece."""
    from clearmd.backend.services.conversion.pdf.latex.layout import layout

    end = closer.left if closer is not None else max(node.right for node in nodes)
    inside = [
        node for node in nodes
        if node is not opener and node is not closer
        and node.left >= opener.right - 0.2 * size and node.right <= end + 0.2 * size
        and opener.bottom - 0.2 * size <= node.axis <= opener.top + 0.2 * size
    ]  # fmt: skip
    inner = layout(inside, [], depth + 1) if inside else ""
    right = rf"\right{DELIMITERS[closer.char]}" if closer is not None else r"\right."
    members = [opener, *inside, *([closer] if closer is not None else [])]
    built = Node(
        rf"\left{DELIMITERS[opener.char]} {inner} {right}",
        opener.left,
        max(node.right for node in members),
        min(node.bottom for node in members),
        max(node.top for node in members),
        size,
        opener.middle,
        tall=True,
    )
    gone = {id(node) for node in members}
    return [*(node for node in nodes if id(node) not in gone), built]


def _level(opener: Node, closer: Node) -> bool:
    overlap = min(opener.top, closer.top) - max(opener.bottom, closer.bottom)
    shorter = min(opener.top - opener.bottom, closer.top - closer.bottom)
    return shorter > 0 and overlap >= SAME_HEIGHT * shorter
