r"""Where a conditional closes among sibling nodes (``\iffalse … \fi`` hides what is between)."""

import re
from typing import Any

from pylatexenc.latexwalker import LatexMacroNode

_CONDITIONAL_NAME = re.compile(r"if(?!thenelse)[A-Za-z@]*")


def matching_fi(nodes: list[Any], start: int) -> int | None:
    r"""The index of the sibling ``\fi`` closing a conditional opened before ``start``."""
    depth = 1
    for index in range(start, len(nodes)):
        node = nodes[index]
        if isinstance(node, LatexMacroNode):
            if node.macroname == "fi":
                depth -= 1
                if depth == 0:
                    return index
            elif _CONDITIONAL_NAME.fullmatch(node.macroname):
                depth += 1
    return None
