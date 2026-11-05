"""``\\href``, ``\\url`` and citations: a link only when its address is safe to open."""

import re
from typing import Any

from clearmd.backend.services.conversion.markdown_out import (
    ENTITY,
    SAFE_LINK,
    escape_text,
    inline_code,
    link_target,
)
from clearmd.backend.services.conversion.tex.nodes import argument, raw
from clearmd.backend.services.conversion.tex.writer.state import RenderState, Writer


def link(w: Writer, node: Any) -> str:
    """``\\href{url}{text}`` or ``\\url{url}``: a link, an autolink or the address as code."""
    url = raw(argument(node, 0)).strip()
    text = w.inline(w.arg_nodes(node, 1)) if node.macroname == "href" else ""
    # "javascript&#58;" is "javascript:" once a viewer decodes it.
    safe = bool(SAFE_LINK.match(url)) and not ENTITY.search(url)
    if node.macroname == "url":
        if not url:
            return ""
        # <…> is an autolink only with a scheme ("<texto>" would be an HTML tag); any other
        # \url is shown as code.
        absolute = re.match(r"(?:https?|ftp|mailto):", url, re.IGNORECASE)
        if safe and absolute and not re.search(r"[\s<>\x00-\x1f\x7f]", url):
            return f"<{url}>"
        return inline_code(url)
    if not url:
        return text
    if not safe:  # javascript: and friends never become links
        return f"{text} ({inline_code(url)})" if text else inline_code(url)
    return f"[{text or escape_text(url)}]({link_target(url)})"


def citation(state: RenderState, node: Any) -> str:
    """``\\cite``-like commands as Pandoc citations: ``[before @key; @other, after]``."""
    written = state.esc(raw(argument(node, 3)))
    keys = [key.strip() for key in written.split(",") if key.strip()]
    if not keys:
        return ""
    first = state.esc(raw(argument(node, 1)).strip())
    second = state.esc(raw(argument(node, 2)).strip())
    before, after = (first, second) if argument(node, 2) is not None else ("", first)
    cited = "; ".join(f"@{key}" for key in keys)
    return "[" + (f"{before} " if before else "") + cited + (f", {after}" if after else "") + "]"
