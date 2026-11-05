"""``itemize``, ``enumerate`` and ``description``: tight Markdown lists, nested ones included.

It stands alone because it is the only module that splits a node list into items.
"""

import re
from typing import Any

from clearmd.backend.services.conversion.markdown_out import MARK, indent, neutralize, outside_code
from clearmd.backend.services.conversion.tex.nodes import is_macro
from clearmd.backend.services.conversion.tex.writer.conditionals import without_false
from clearmd.backend.services.conversion.tex.writer.state import Writer


def list_block(w: Writer, node: Any) -> str:
    """The list environment ``node`` as Markdown items, with what comes before the first item."""
    before: list[Any] = []
    items: list[tuple[Any, list[Any]]] = []
    for child in without_false(list(node.nodelist or []), w.state.recovered):
        if is_macro(child, "item"):
            items.append((child, []))
        elif items:
            items[-1][1].append(child)
        else:
            before.append(child)
    lines = []
    for number, (item, content) in enumerate(items, start=1):
        marker = f"{number}. " if node.environmentname == "enumerate" else "- "
        text = w.render(content).strip()
        if node.environmentname == "description":
            term = w.inline(w.arg_nodes(item, 0))
            text = f"**{term}** {text}" if term else text
        # Tight items, nested lists included; code inside an item keeps its blank lines.
        text = outside_code(text, lambda part: re.sub(r"\n[ \t]*\n+", "\n", part))
        text = neutralize(text, keep_marks=True)  # "\\item # x" is not a heading in an item
        lines.append(MARK + marker + indent(text, len(marker)))
    intro = w.render(before).strip()
    listed = "\n".join(lines)
    return f"{intro}\n\n{listed}" if intro else listed
