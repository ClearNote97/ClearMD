"""The title block: ``\\title``, ``\\author`` and ``\\date``, shown where ``\\maketitle`` is.

It stands alone because it is the only reader of the preamble's metadata.
"""

from typing import Any

from pylatexenc.latexwalker import LatexMacroNode

from clearmd.backend.services.conversion.markdown_out import MARK, block
from clearmd.backend.services.conversion.tex.nodes import walk
from clearmd.backend.services.conversion.tex.writer.state import Writer
from clearmd.backend.services.conversion.tex.writer.vocab import METADATA


def scan_metadata(w: Writer, preamble: list[Any]) -> None:
    """Keep the arguments of ``\\title``, ``\\author`` and ``\\date`` found in ``preamble``."""
    for node in walk(preamble):
        if isinstance(node, LatexMacroNode) and node.macroname in METADATA:
            w.state.metadata[node.macroname] = w.last_arg(node)


def title_block(w: Writer) -> str:
    """The title block, written in text mode even inside ``\\texttt``."""
    with w.state.text_mode():
        return title_text(w)


def title_text(w: Writer) -> str:
    """``# title`` and, under it, the author and date; nothing without a title."""
    title = w.inline(w.state.metadata.get("title", []))
    if not title:
        return ""
    byline = " · ".join(
        part for part in (w.inline(w.state.metadata.get(k, [])) for k in ("author", "date")) if part
    )
    return block(f"{MARK}# {title}" + (f"\n\n{MARK}*{byline}*" if byline else ""))
