"""Dispatch: which writer a block element goes to, and the nesting limit that stops the rest.

It stands alone because it is the one module that knows every kind of block.
"""

from clearmd.backend.services.conversion.html.writer.blocks import (
    code_block,
    heading_block,
    quote_block,
)
from clearmd.backend.services.conversion.html.writer.lists import list_block
from clearmd.backend.services.conversion.html.writer.runs import inline_of
from clearmd.backend.services.conversion.html.writer.state import MAX_NESTING, Writer
from clearmd.backend.services.conversion.html.writer.tables import table_block
from clearmd.backend.services.conversion.markdown_out import block, escape_text
from clearmd.backend.services.conversion.xmltree import Element


def write_block(w: Writer, element: Element) -> str:
    tag = element.tag
    if w.state.depth >= MAX_NESTING:
        w.state.note_unknown(tag)
        text = escape_text(" ".join(element.text().split()))
        return block(text) if text else ""
    w.state.depth += 1
    try:
        if tag == "head":
            return heading_block(w, element)
        if tag == "p":
            text = inline_of(w, element.children)
            return block(text) if text else ""
        if tag == "list":
            return block(list_block(w, element, 1))
        if tag == "quote":
            return quote_block(w, element)
        if tag == "code":
            return code_block(w, element)
        if tag == "table":
            return table_block(w, element)
        return w.blocks(list(element.children))  # div, ab: their content
    finally:
        w.state.depth -= 1
