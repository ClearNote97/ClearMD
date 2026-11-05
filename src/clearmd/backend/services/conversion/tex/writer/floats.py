"""Figures and tables: which environments are floats and which caption belongs to which."""

from typing import Any

from pylatexenc.latexwalker import LatexEnvironmentNode

from clearmd.backend.services.conversion.tex.nodes import is_macro, walk
from clearmd.backend.services.conversion.tex.writer.vocab import FLOATS


def is_float(node: Any) -> bool:
    """Whether ``node`` is a figure or table, or a minipage holding its own caption."""
    if not isinstance(node, LatexEnvironmentNode):
        return False
    if node.environmentname in FLOATS:
        return True
    return node.environmentname == "minipage" and own_caption(node) is not None


def own_caption(node: Any) -> Any:
    """The first ``\\caption`` of a float, not looking into the floats inside it."""
    for found in walk(node.nodelist, skip=is_float):
        if is_macro(found, "caption"):
            return found
    return None
