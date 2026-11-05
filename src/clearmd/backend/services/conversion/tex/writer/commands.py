"""``\\command`` nodes: the ordered chain that decides what each command becomes.

The order of the tests is behaviour: an author's macro goes first, then sectioning, styles and so
on down to "unknown". Do not reorder.
"""

from typing import Any

from pylatexenc.latex2text import LatexNodes2Text, get_default_latex_context_db

from clearmd.backend.services.conversion.markdown_out import MARK, block, inline_code
from clearmd.backend.services.conversion.tex.macros import is_parametrized_def
from clearmd.backend.services.conversion.tex.nodes import argument, raw
from clearmd.backend.services.conversion.tex.parsing import CITATION_MACROS, REFERENCE_MACROS
from clearmd.backend.services.conversion.tex.writer.expansion import expanded
from clearmd.backend.services.conversion.tex.writer.floats import include_left, picture
from clearmd.backend.services.conversion.tex.writer.front_matter import title_block
from clearmd.backend.services.conversion.tex.writer.links import citation, link
from clearmd.backend.services.conversion.tex.writer.state import Writer
from clearmd.backend.services.conversion.tex.writer.vocab import (
    DROPPED,
    INCLUDES,
    INLINE,
    METADATA,
    PLAIN,
    SECTION_LEVELS,
    WORDS,
)

_LATEX2TEXT = LatexNodes2Text(math_mode="verbatim", strict_latex_spaces=False)
_LATEX2TEXT_DB = get_default_latex_context_db()


def macro(w: Writer, node: Any) -> str:
    """The Markdown of one command; an unknown one is kept as written and noted."""
    name: str = node.macroname
    if w.state.macros is not None and w.state.macros.knows(name):
        return expanded(w.state, node, w.render)
    if name in SECTION_LEVELS:
        level = 2 + max(0, SECTION_LEVELS[name] - w.state.level)
        return block(MARK + "#" * min(6, level) + " " + w.inline(w.last_arg(node)))
    if name in INLINE:
        content = w.inline(w.last_arg(node))
        return INLINE[name].format(content) if content else ""
    if name == "texttt":
        w.state.in_code += 1
        try:
            content = w.inline(w.last_arg(node))
        finally:
            w.state.in_code -= 1
        return inline_code(content) if content else ""
    if name in PLAIN:
        return w.render(w.last_arg(node))
    if name in METADATA:
        w.state.metadata[name] = w.last_arg(node)
        return ""
    if name == "maketitle":
        return title_block(w)
    if name in {"href", "url"}:
        return link(w, node)
    if name == "verb":
        code = getattr(node.nodeargd, "verbatim_text", None)
        return inline_code(code) if code is not None else w.state.note_unknown("\\verb", node)
    if name == "footnote":
        with w.state.text_mode():
            w.state.footnotes.append(w.inline(w.last_arg(node)))
        return f"[^{len(w.state.footnotes)}]"
    if name in CITATION_MACROS:
        return citation(w.state, node)
    if name in REFERENCE_MACROS:
        return f"({w.state.esc(raw(argument(node, 0)).strip())})"
    if name == "includegraphics":
        return picture(w.state, node)
    if name == "caption":
        if id(node) in w.state.consumed:
            return ""
        return block(f"*{w.inline(w.last_arg(node))}*")
    if name in INCLUDES:
        return include_left(w.state, node)
    if name == "def":
        return w.state.note_unknown("\\def", node) if is_parametrized_def(node) else ""
    if name == "\\":
        return "  \n"
    if name == "par":
        return "\n\n"
    if name == "and":
        return ", "
    if name in DROPPED:
        return ""
    if name in WORDS:
        return WORDS[name]
    if _LATEX2TEXT_DB.get_macro_spec(name) is not None:
        return w.state.esc(str(_LATEX2TEXT.nodelist_to_text([node])))
    return w.state.note_unknown(f"\\{name}", node)
