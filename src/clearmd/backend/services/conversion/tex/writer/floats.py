"""Figures and tables: which environments are floats, their captions, images and tables."""

from typing import Any

from pylatexenc.latexwalker import LatexEnvironmentNode

from clearmd.backend.schemas.notes import NoteItem, NoteReason
from clearmd.backend.services.conversion.markdown_out import (
    MARK,
    block,
    fence_for,
    inline_code,
    link_target,
)
from clearmd.backend.services.conversion.tex.nodes import argument, is_macro, raw, walk
from clearmd.backend.services.conversion.tex.tables import tabular_to_markdown
from clearmd.backend.services.conversion.tex.writer.state import RenderState, Writer
from clearmd.backend.services.conversion.tex.writer.vocab import FLOATS, MAX_UNKNOWN


def is_float(node: Any) -> bool:
    """Whether ``node`` is a figure or table, or a minipage holding its own caption."""
    if not isinstance(node, LatexEnvironmentNode):
        return False
    if node.environmentname in FLOATS:
        return True
    return node.environmentname == "minipage" and own_caption(node) is not None


def own_caption(node: Any) -> Any:
    """The first ``\\caption`` of a float, not looking into the floats inside it."""
    for found in walk(node.nodelist, skip=is_float):
        if is_macro(found, "caption"):
            return found
    return None


def picture(state: RenderState, node: Any) -> str:
    """``\\includegraphics`` as an image link; outside the folder or remote it is only shown."""
    path = raw(argument(node, -1)).strip()
    target = state.image(path)
    if target is None:  # outside the folder or remote: shown, never fetched by a viewer
        return inline_code(node.latex_verbatim().strip())
    alt = state.alt[-1] if state.alt else ""
    return f"![{alt}]({link_target(target)})"


def float_block(w: Writer, node: Any) -> str:
    """A figure or table: its content in order; the caption on its only image, or under it."""
    caption_node = own_caption(node)
    with w.state.text_mode():
        caption = w.inline(w.last_arg(caption_node)) if caption_node else ""
    if caption_node is not None:
        w.state.consumed.add(id(caption_node))
    images = [n for n in walk(node.nodelist, skip=is_float) if is_macro(n, "includegraphics")]
    if len(images) == 1 and caption:
        w.state.alt.append(caption)
        try:
            return block(w.render(node.nodelist or []))
        finally:
            w.state.alt.pop()
    w.state.alt.append("")
    try:
        body = w.render(node.nodelist or [])
    finally:
        w.state.alt.pop()
    return block(body) + (block(f"*{caption}*") if caption else "")


def tabular(w: Writer, node: Any) -> str:
    """A ``tabular`` as a Markdown table, or kept as LaTeX when it has no such form."""
    captions = [child for child in node.nodelist or [] if is_macro(child, "caption")]
    w.state.consumed.update(id(caption) for caption in captions)
    caption = w.inline(w.last_arg(captions[0])) if captions else ""
    table = tabular_to_markdown(node, w.inline)
    if table is None:
        w.state.tables_kept += 1
        source = node.latex_verbatim()
        fence = fence_for(source)
        table = f"{MARK}{fence}latex\n{source}\n{MARK}{fence}"
    return block(table) + (block(f"*{caption}*") if caption else "")


def include_left(state: RenderState, node: Any) -> str:
    """An include still in the text: refused while reading (noted there) or made by a macro."""
    subject = raw(argument(node, 0)).strip()
    if state.listed + len(state.refused) < MAX_UNKNOWN:
        if state.macros is not None and state.macros.depth > 0:
            state.refused[NoteItem(subject, NoteReason.MADE_BY_MACRO.value)] = None
        elif subject not in state.known_refused:  # "\\input{{ch}}": no file has that name
            state.refused[NoteItem(subject, NoteReason.MISSING.value)] = None
    return inline_code(node.latex_verbatim().strip())
