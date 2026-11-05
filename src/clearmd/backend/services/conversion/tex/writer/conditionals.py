r"""Where a conditional closes among sibling nodes (``\iffalse … \fi`` hides what is between)."""

import re
from typing import Any

from pylatexenc.latexwalker import LatexMacroNode

from clearmd.backend.services.conversion.tex.nodes import is_macro

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


def without_false(nodes: list[Any], recovered: dict[str, None]) -> list[Any]:
    """``nodes`` without what ``\\iffalse … \\fi`` comments out (nested conditionals
    counted); an ``\\iffalse`` without its ``\\fi`` hides nothing and is noted."""
    kept: list[Any] = []
    index = 0
    while index < len(nodes):
        node = nodes[index]
        if is_macro(node, "iffalse"):
            closing = matching_fi(nodes, index + 1)
            if closing is not None:
                index = closing + 1
                continue
            recovered["\\iffalse without its \\fi"] = None
        kept.append(node)
        index += 1
    return kept
