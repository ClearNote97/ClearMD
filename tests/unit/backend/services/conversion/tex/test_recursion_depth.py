"""How many Python frames each TeX nesting level costs the renderer (refactor R01, risk R14).

The converter falls back to "kept as LaTeX" when a nesting makes the interpreter run out of
stack, so the nesting depth where that starts depends on the frames used per level. The tests
find, for each kind of nesting, the smallest recursion limit that still converts the document
(parsing runs unrestricted, so only the rendering is measured, in a fresh thread) and pin how
much that limit grows per level. A change in the call structure moves these numbers.
"""

import sys
import threading
from collections.abc import Callable
from typing import Any
from unittest.mock import patch

import pytest

from clearmd.backend.services.conversion.tex import render

HIGH = 100_000
LOW, SHALLOW, DEEP = 5, 40, 80  # lowest limit tried; the two nesting depths compared
MACRO = "\\newcommand{\\b}[1]{(#1)}"


def _kept_whole(latex: str, limit: int) -> bool:
    """Whether rendering ``latex`` under ``limit`` frames falls back to a LaTeX code block."""
    original = vars(render)["parse"]
    outcome: list[bool] = []

    def parse_freely(*args: Any, **kwargs: Any) -> Any:
        sys.setrecursionlimit(HIGH)
        try:
            return original(*args, **kwargs)
        finally:
            sys.setrecursionlimit(limit)

    def work() -> None:
        outcome.append(render.render_source(latex).markdown.startswith("```latex"))

    previous = sys.getrecursionlimit()
    try:
        with patch.object(render, "parse", parse_freely):
            thread = threading.Thread(target=work)
            thread.start()
            thread.join()
    finally:
        sys.setrecursionlimit(previous)
    return outcome[0]


def _needed(latex: str) -> int:
    """The smallest recursion limit under which ``latex`` is converted, not kept whole."""
    low, high = LOW, 20_000
    assert not _kept_whole(latex, high)
    while low < high:
        middle = (low + high) // 2
        if _kept_whole(latex, middle):
            low = middle + 1
        else:
            high = middle
    return low


def _wrap(opening: str, closing: str) -> Callable[[int], str]:
    return lambda depth: opening * depth + "x" + closing * depth


def _math_groups(depth: int) -> str:
    return "$" + "{" * depth + "% c\n x" + "}" * depth + "$"  # a comment forces the rewrite


def _math_macros(depth: int) -> str:
    return MACRO + "$" + "\\b{" * depth + "x" + "}" * depth + "$"


# family -> (the nesting at a depth, frames the needed limit grows per level)
FAMILIES: dict[str, tuple[Callable[[int], str], int]] = {
    "groups": (_wrap("{", "}"), 2),
    "quotes": (_wrap("\\begin{quote}", "\\end{quote}"), 3),
    "lists": (_wrap("\\begin{itemize}\\item ", "\\end{itemize}"), 4),
    "descriptions": (_wrap("\\begin{description}\\item[a] ", "\\end{description}"), 4),
    "figures": (_wrap("\\begin{figure}", "\\end{figure}"), 4),
    "bold": (_wrap("\\textbf{", "}"), 4),
    "footnotes": (_wrap("\\footnote{", "}"), 4),
    "links": (_wrap("\\href{u}{", "}"), 5),
    "math_groups": (_math_groups, 1),
    "math_macros": (_math_macros, 6),
}


@pytest.mark.parametrize("name", sorted(FAMILIES))
def test_each_nesting_level_costs_the_same_frames_as_before(name: str) -> None:
    build, per_level = FAMILIES[name]
    grown = _needed(build(DEEP)) - _needed(build(SHALLOW))
    assert grown == per_level * (DEEP - SHALLOW)
