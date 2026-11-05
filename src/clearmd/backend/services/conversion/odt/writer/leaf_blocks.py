"""Leaf blocks: quotes, code and tables, the blocks that hold paragraphs only."""

from functools import partial

from clearmd.backend.services.conversion.inline import LINE_BREAK
from clearmd.backend.services.conversion.markdown_out import MARK, block, fence_for
from clearmd.backend.services.conversion.odt.tables import table_to_markdown
from clearmd.backend.services.conversion.odt.writer.inline import plain_text
from clearmd.backend.services.conversion.odt.writer.paragraphs import (
    hidden,
    own_paragraphs,
    paragraph_props,
)
from clearmd.backend.services.conversion.odt.writer.state import Writer
from clearmd.backend.services.conversion.xmltree import Element


def quote_block(w: Writer, paragraphs: list[Element]) -> str:
    lines = []
    for paragraph in paragraphs:
        if hidden(w, paragraph):
            continue
        text = w.inline(paragraph, paragraph_props(w, paragraph))
        lines.append(f"{MARK}> {text}" if text else f"{MARK}>")
    if not lines:
        return ""
    return block("\n".join(lines))


def code_block(w: Writer, paragraphs: list[Element]) -> str:
    shown = [paragraph for paragraph in paragraphs if not hidden(w, paragraph)]
    if not shown:
        return ""
    code = "\n".join(plain_text(w, paragraph) for paragraph in shown).strip("\n")
    fence = fence_for(code)
    return block(f"{MARK}{fence}\n{code}\n{MARK}{fence}")


def table_block(w: Writer, table: Element) -> str:
    found = table_to_markdown(table, partial(cell_text, w), w.state.spend)
    if found.simplified:
        w.state.counts.tables_simplified += 1
    return block(found.markdown) if found.markdown else ""


def cell_text(w: Writer, cell: Element) -> str:
    shown = [p for p in own_paragraphs(w, cell) if not hidden(w, p)]
    texts = [w.inline(p, paragraph_props(w, p)) for p in shown]
    return " ".join(text.replace(LINE_BREAK, " ") for text in texts if text)
