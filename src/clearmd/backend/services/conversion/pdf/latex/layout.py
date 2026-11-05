"""The dispatcher: fractions, accents, limits, brackets, then rows (feature 015)."""

from collections import Counter

from clearmd.backend.services.conversion.pdf.latex.accents import accents
from clearmd.backend.services.conversion.pdf.latex.brackets import brackets
from clearmd.backend.services.conversion.pdf.latex.fractions import fractions
from clearmd.backend.services.conversion.pdf.latex.nodes import Bar, Node
from clearmd.backend.services.conversion.pdf.latex.operators import limits
from clearmd.backend.services.conversion.pdf.latex.rows import text_rows
from clearmd.backend.services.conversion.pdf.latex.symbols import BIG_OPERATORS, CLOSERS, OPENERS
from clearmd.backend.services.conversion.pdf.latex.unsure import Unsure

MAX_DEPTH = 8  # fractions, brackets and scripts inside one another
MAX_ROWS = 12  # an equation's rows (a system of constraints) at most
TEXT_SHARE = 0.1  # of an equation's pieces: a size this many have may be its text's


def layout(nodes: list[Node], bars: list[Bar], depth: int) -> str:
    """The pieces as LaTeX: fractions first (each bar's numerator and denominator), then tall
    brackets with what they hold, then the rows, each piece with its scripts."""
    if depth > MAX_DEPTH:
        raise Unsure
    if not nodes:
        return ""
    nodes = fractions(nodes, bars, depth)
    size = _text_size(nodes)
    nodes = accents(nodes, size)
    nodes = limits(nodes, size, depth)
    nodes = brackets(nodes, size, depth)
    rows = text_rows(nodes, size, depth)
    if len(rows) > MAX_ROWS:
        raise Unsure
    if len(rows) == 1:
        return rows[0]
    # Each row in display style: its fractions and sums as large as on the page.
    return (
        r"\begin{array}{l} "
        + r" \\ ".join(rf"\displaystyle {row}" for row in rows)
        + r" \end{array}"
    )


def _text_size(nodes: list[Node]) -> float:
    """The text's size: the largest one a fair share of the pieces have (an equation may hold
    more script than text: "(x^{t+1}, y^{t+1})"); never a sum's or a tall bracket's."""
    sizes = Counter(
        round(node.size, 1) for node in nodes
        if not node.tall and node.char not in BIG_OPERATORS
        and node.char not in OPENERS and node.char not in CLOSERS
    )  # fmt: skip
    if not sizes:
        return max(node.size for node in nodes)
    total = sum(sizes.values())
    shared = [size for size, count in sizes.items() if count >= TEXT_SHARE * total]
    return max(shared, default=sizes.most_common(1)[0][0])
