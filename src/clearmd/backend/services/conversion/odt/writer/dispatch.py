"""Dispatch: which writer a block-level element goes to (the order of the tests is behaviour).

It stands alone because it is the one module that knows every kind of block: the others know one.
"""

from clearmd.backend.services.conversion.markdown_out import block, escape_text
from clearmd.backend.services.conversion.odt.writer.frames import frame_markdown
from clearmd.backend.services.conversion.odt.writer.leaf_blocks import table_block
from clearmd.backend.services.conversion.odt.writer.lists import list_block
from clearmd.backend.services.conversion.odt.writer.paragraphs import heading_block, paragraph_block
from clearmd.backend.services.conversion.odt.writer.state import Writer
from clearmd.backend.services.conversion.odt.writer.vocab import DROPPED_BLOCKS
from clearmd.backend.services.conversion.xmltree import Element


def write_block(w: Writer, element: Element) -> str:
    tag = element.tag
    if tag == "text:p":
        return paragraph_block(w, element)
    if tag == "text:h":
        return heading_block(w, element)
    if tag == "text:list":
        return block(list_block(w, element, 1, ""))
    if tag == "table:table":
        return table_block(w, element)
    if tag in {"draw:frame", "draw:a"}:  # a page-anchored frame sits directly in the text
        frames = [element] if tag == "draw:frame" else list(element.elements("draw:frame"))
        return block(" ".join(frame_markdown(w, frame) for frame in frames))
    if tag == "text:section":
        if element.get("text:display") == "none":
            return ""
        return w.blocks(list(element.elements()))
    if tag == "text:tracked-changes":
        w.state.counts.changes += sum(1 for _ in element.elements("text:changed-region"))
        return ""
    if tag in DROPPED_BLOCKS:
        return ""
    w.state.note_unknown(tag)
    return block(escape_text(" ".join(element.text().split())))
