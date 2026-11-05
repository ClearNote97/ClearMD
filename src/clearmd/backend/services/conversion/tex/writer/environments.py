"""``\\begin{…}`` environments: containers, abstract, quotes, code, math, floats and tables."""

import re
from typing import Any

from clearmd.backend.services.conversion.markdown_out import MARK, block, fence_for, neutralize
from clearmd.backend.services.conversion.tex.writer.floats import float_block, is_float, tabular
from clearmd.backend.services.conversion.tex.writer.lists import list_block
from clearmd.backend.services.conversion.tex.writer.math import display, math_body
from clearmd.backend.services.conversion.tex.writer.state import Writer
from clearmd.backend.services.conversion.tex.writer.vocab import (
    ALIGNED,
    CODE,
    CONTAINERS,
    DISPLAY_MATH,
    LISTS,
    QUOTES,
    TABULARS,
)


def environment(w: Writer, node: Any) -> str:
    """The Markdown of one environment; an unknown one is kept as written and noted."""
    name: str = node.environmentname
    if name == "comment":
        return ""
    if name in CONTAINERS or (name == "minipage" and not is_float(node)):
        return w.render(node.nodelist or [])
    if name == "abstract":
        heading = "Resumen" if w.state.spanish else "Abstract"
        return block(f"{MARK}## {heading}") + block(w.render(node.nodelist or []))
    if name in LISTS:
        return block(list_block(w, node))
    if name in QUOTES:
        body = neutralize(w.render(node.nodelist or []).strip(), keep_marks=True)
        quoted = (f"{MARK}> {line}" if line else f"{MARK}>" for line in body.split("\n"))
        return block("\n".join(quoted))
    if name in CODE:
        return block(code_block(node))
    if name in DISPLAY_MATH:
        return block(display(math_body(w.state, node.nodelist)))
    if name in ALIGNED:
        inner = ALIGNED[name]
        body = math_body(w.state, node.nodelist)
        return block(display(f"\\begin{{{inner}}}\n{body}\n\\end{{{inner}}}"))
    if is_float(node):
        return float_block(w, node)
    if name in TABULARS:
        return tabular(w, node)
    return w.state.note_unknown(f"\\begin{{{name}}}", node)


def code_block(node: Any) -> str:
    """A verbatim environment as a fenced block; ``lstlisting`` and ``minted`` name a language."""
    found = getattr(node.nodeargd, "verbatim_text", None) if node.nodeargd else None
    code_text: str = found or ""
    language = ""
    if node.environmentname == "lstlisting":
        options = re.match(r"\s*\[([^\]\n]{0,1024})\]", code_text)
        if options:
            code_text = code_text[options.end() :]
            declared = re.search(r"language\s*=\s*\{?([\w+#-]+)", options.group(1))
            language = declared.group(1).lower() if declared else ""
    elif node.environmentname == "minted":
        declared = re.match(r"\s*(?:\[[^\]\n]{0,1024}\])?\s*\{([^}\n]{0,64})\}", code_text)
        if declared:
            code_text = code_text[declared.end() :]
            language = declared.group(1).strip().lower()
    code = code_text.strip("\n")
    fence = fence_for(code)
    return f"{MARK}{fence}{language}\n{code}\n{MARK}{fence}"
