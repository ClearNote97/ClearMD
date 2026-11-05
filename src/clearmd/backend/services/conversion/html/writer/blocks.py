"""Blocks: headings, quotations and code, the blocks that are not lists or tables."""

import re

from clearmd.backend.services.conversion.html.writer.runs import inline_of
from clearmd.backend.services.conversion.html.writer.shapes import code_text, one_line
from clearmd.backend.services.conversion.html.writer.state import Writer
from clearmd.backend.services.conversion.inline import TextProps
from clearmd.backend.services.conversion.markdown_out import (
    MARK,
    block,
    fence_for,
    heading_text,
    neutralize,
    outside_code,
    own_line,
)
from clearmd.backend.services.conversion.xmltree import Element, int_attribute


def heading_block(w: Writer, element: Element) -> str:
    if not element.get("rend"):  # a heading without a level (a summary): bold, not a heading
        text = one_line(inline_of(w, element.children, TextProps(bold=True)))
        return block(text) if text else ""
    text = one_line(inline_of(w, element.children))
    if not text:
        return ""
    level = int_attribute(element.get("rend")[1:], w.state.top, cap=6)
    hashes = "#" * min(6, 2 + max(0, level - w.state.top))
    return block(f"{MARK}{hashes} {heading_text(text)}")


def quote_block(w: Writer, element: Element) -> str:
    inner = w.blocks(list(element.children)).strip("\n")
    inner = outside_code(inner, lambda part: re.sub(r"\n{3,}", "\n\n", part))
    if not inner:
        return ""
    lines = neutralize(inner, keep_marks=True).split("\n")
    quoted = (f"{MARK}> {own_line(line)}" if line else f"{MARK}>" for line in lines)
    return block("\n".join(quoted))


def code_block(w: Writer, element: Element) -> str:
    code = code_text(element).strip("\n")
    if not code.strip() or not w.state.spend(len(code)):
        return ""
    fence = fence_for(code)
    return block(f"{MARK}{fence}\n{code}\n{MARK}{fence}")
