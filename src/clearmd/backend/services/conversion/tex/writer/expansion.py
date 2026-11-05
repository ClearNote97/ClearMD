"""The use of an author's macro, expanded under the budget: shared by commands and math."""

from collections.abc import Callable
from typing import Any

from clearmd.backend.services.conversion.tex.macros import BudgetExceeded
from clearmd.backend.services.conversion.tex.writer.state import RenderState


def expanded(
    state: RenderState, node: Any, serialize: Callable[[list[Any]], str], *, math: bool = False
) -> str:
    """A use of an author's macro, expanded; past the budget the top-level use stays as is."""
    assert state.macros is not None
    top = state.macros.depth == 0
    try:
        with state.macros.nested():
            return serialize(state.macros.expand(node))
    except BudgetExceeded:
        if not top:
            raise
        if state.macros.limited is None:
            state.macros.limited = f"\\{node.macroname}"
        written: str = node.latex_verbatim()
        return written if math else state.esc(written)
