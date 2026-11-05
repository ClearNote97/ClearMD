r"""The renderer: walks nodes in order and hands each one to the module that writes it.

``Renderer`` is the only recursive entry point (``render`` → ``_node`` → a command or environment
writer → ``render`` again). The writers are plain functions that take the renderer, so a level of
TeX nesting costs the same Python frames as when they were methods: the depth at which a deep
source falls back to a LaTeX code block must not move.
"""

import re
from typing import Any

from pylatexenc.latexwalker import (
    LatexCharsNode,
    LatexCommentNode,
    LatexEnvironmentNode,
    LatexGroupNode,
    LatexMacroNode,
    LatexMathNode,
    LatexSpecialsNode,
)

from clearmd.backend.services.conversion.markdown_out import (
    MARK,
    block,
    ends_a_line,
    escape_text,
    join_pieces,
    tidy,
)
from clearmd.backend.services.conversion.tex.macros import BudgetExceeded, MacroExpander
from clearmd.backend.services.conversion.tex.nodes import argument
from clearmd.backend.services.conversion.tex.writer.commands import macro
from clearmd.backend.services.conversion.tex.writer.conditionals import without_false
from clearmd.backend.services.conversion.tex.writer.environments import environment
from clearmd.backend.services.conversion.tex.writer.front_matter import scan_metadata
from clearmd.backend.services.conversion.tex.writer.math import math_node
from clearmd.backend.services.conversion.tex.writer.state import ImageHandler, RenderState
from clearmd.backend.services.conversion.tex.writer.structure import split_document
from clearmd.backend.services.conversion.tex.writer.vocab import SECTION_LEVELS, SPECIALS

_INDENTATION = re.compile(r"\n[ \t]+")


class Renderer:
    """Nodes → Markdown. What a run accumulates lives in ``state``."""

    def __init__(
        self,
        *,
        level: int = SECTION_LEVELS["section"],
        spanish: bool = False,
        image: ImageHandler | None = None,
        macros: MacroExpander | None = None,
        known_refused: frozenset[str] = frozenset(),
        listed: int = 0,
    ) -> None:
        self.state = RenderState(
            level=level,
            spanish=spanish,
            image=image,
            macros=macros,
            known_refused=known_refused,
            listed=listed,
        )

    # --- Entry points -------------------------------------------------------------------------

    def document(self, nodes: list[Any]) -> str:
        """The whole document: its metadata read from the preamble, then the body and footnotes."""
        preamble, body = split_document(nodes)
        if body is not preamble:
            scan_metadata(self, preamble)
        text = self.render(body)
        if self.state.footnotes:
            notes = "\n".join(
                f"{MARK}[^{n}]: {note}" for n, note in enumerate(self.state.footnotes, start=1)
            )
            text += block(notes)
        return tidy(text)

    def render(self, nodes: list[Any]) -> str:
        """The Markdown of ``nodes``, block structure kept."""
        parts: list[str] = []
        after_unknown = False
        for node in without_false(nodes, self.state.recovered):
            if node is None:
                continue
            if after_unknown and isinstance(node, LatexGroupNode):
                parts.append(self.state.esc(node.latex_verbatim()))  # its arguments, as written
                continue
            before = len(self.state.unknown)
            piece = self._node(node)
            if isinstance(node, LatexCharsNode) and ends_a_line(parts):
                piece = piece.lstrip(" \t")  # "\\section{A}    Text" is not a code block
            parts.append(piece)
            after_unknown = isinstance(node, LatexMacroNode) and len(self.state.unknown) > before
        return join_pieces(parts)

    def inline(self, nodes: list[Any]) -> str:
        """The Markdown of ``nodes`` on one line."""
        return re.sub(r"\s+,", ",", " ".join(self.render(nodes).split()))

    # --- Nodes ------------------------------------------------------------------------------

    def _node(self, node: Any) -> str:
        if isinstance(node, LatexCharsNode):
            if self.state.in_code:
                return str(node.chars)
            text = _INDENTATION.sub("\n", str(node.chars))  # never an indented code block
            return escape_text(text)
        if isinstance(node, LatexCommentNode):
            return ""
        if isinstance(node, LatexSpecialsNode):
            chars = str(node.specials_chars)
            return chars if self.state.in_code else SPECIALS.get(chars, chars)
        if isinstance(node, LatexGroupNode):
            return self.render(node.nodelist or [])
        if isinstance(node, LatexMathNode):
            return math_node(self.state, node)
        if isinstance(node, LatexMacroNode | LatexEnvironmentNode):
            try:
                if isinstance(node, LatexMacroNode):
                    return macro(self, node)
                return environment(self, node)
            except (BudgetExceeded, RecursionError, MemoryError):
                raise
            except Exception as problem:  # one bad command, not the whole document (AC-21)
                name = getattr(node, "macroname", None) or f"{{{node.environmentname}}}"
                self.state.recovered[f"\\{name}: {type(problem).__name__}"] = None
                return self.state.esc(node.latex_verbatim())
        return ""

    def arg_nodes(self, node: Any, index: int) -> list[Any]:
        """The nodes inside argument ``index`` of ``node`` (none when it is missing)."""
        found = argument(node, index)
        if found is None:
            return []
        if isinstance(found, LatexGroupNode):
            return list(found.nodelist or [])
        return [found]

    def last_arg(self, node: Any) -> list[Any]:
        """The nodes inside the last argument of ``node``."""
        return self.arg_nodes(node, -1)
