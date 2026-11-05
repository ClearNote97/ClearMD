r"""Math written back as the author wrote it, with the author's macros expanded.

Every function takes the ``RenderState`` only: math never renders text nodes, it re-reads the
source. ``serialize`` and ``math_source`` call each other through the author's macros, so the
macro callback is a ``functools.partial`` (no frame of its own on the recursive path).
"""

import re
from functools import partial
from typing import Any

from pylatexenc.latexwalker import LatexCommentNode, LatexMacroNode

from clearmd.backend.services.conversion.markdown_out import MARK, block, escape_math, math_line
from clearmd.backend.services.conversion.tex.nodes import children, is_macro, walk
from clearmd.backend.services.conversion.tex.writer.expansion import expanded
from clearmd.backend.services.conversion.tex.writer.state import RenderState

_CONTROL_WORD_AT_END = re.compile(r"\\[A-Za-z]+$")


def is_label(node: Any) -> bool:
    """Whether ``node`` is a ``\\label``, which math drops."""
    return is_macro(node, "label")


def math_node(state: RenderState, node: Any) -> str:
    """Inline math as ``$…$``, display math as a ``$$`` block."""
    body = math_body(state, node.nodelist)
    if node.displaytype == "display":
        return block(display(body))
    return f"${body}$"


def display(body: str) -> str:
    """``$$`` lines are ClearMD's; the math between them is never read as Markdown blocks."""
    lines = "\n".join(math_line(line) for line in body.split("\n"))
    return f"{MARK}$$\n{lines}\n{MARK}$$"


def math_body(state: RenderState, nodes: list[Any] | None) -> str:
    """The math of ``nodes`` on one line, escaped for Markdown."""
    return escape_math(" ".join(math_source(state, list(nodes or [])).split()))


# --- Math as written, with the author's macros ----------------------------------------------


def math_source(state: RenderState, nodes: list[Any]) -> str:
    """The source of ``nodes``, labels dropped, the author's macros expanded."""
    return "".join(serialize(state, n) for n in nodes if n is not None and not is_label(n))


def serialize(state: RenderState, node: Any) -> str:
    """Math as written; only comments and spans that use an author's macro are replaced."""
    if isinstance(node, LatexCommentNode):
        return " "  # "% first\nc &= d" must not hide "c &= d" once lines are joined
    verbatim: str = node.latex_verbatim()
    if isinstance(node, LatexMacroNode) and state.knows(node.macroname):
        text = expanded(state, node, partial(math_source, state), math=True)
        # "\\R x" must not become "\\mathbb{R}x" glued to a following letter by mistake.
        if text != verbatim and _CONTROL_WORD_AT_END.search(text):
            text += " "
        return text
    inner = children(node)
    if not any(needs_rewrite(state, child) for child in inner):
        return verbatim
    source: str = node.parsing_state.s
    parts, cursor = [], node.pos
    for child in inner:
        parts.append(source[cursor : child.pos])
        parts.append(serialize(state, child))
        cursor = child.pos + child.len
    parts.append(source[cursor : node.pos + node.len])
    return "".join(parts)


def needs_rewrite(state: RenderState, node: Any) -> bool:
    """Whether ``node`` holds a comment or a use of an author's macro."""
    return any(
        isinstance(found, LatexCommentNode)
        or (isinstance(found, LatexMacroNode) and state.knows(found.macroname))
        for found in walk([node])
    )
