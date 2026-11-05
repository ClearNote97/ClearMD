"""Inline: a paragraph's runs of text with their effective properties; code as written."""

import re
from typing import Any

from clearmd.backend.services.conversion.inline import LINE_BREAK, Piece, Raw, Text, TextProps
from clearmd.backend.services.conversion.odt.writer.footnotes import note_reference
from clearmd.backend.services.conversion.odt.writer.frames import frame_markdown
from clearmd.backend.services.conversion.odt.writer.state import Writer
from clearmd.backend.services.conversion.odt.writer.vocab import (
    DROPPED_INLINE,
    FIELDS,
    MAX_SPACES,
    SPAN_LIKE,
)
from clearmd.backend.services.conversion.xmltree import Element, int_attribute

_WHITESPACE = re.compile(r"[ \t\r\n]+")  # code paragraphs (plain)


def plain_text(w: Writer, paragraph: Element) -> str:
    """A code paragraph's text as written: no escaping, spaces and tabs kept."""
    out = []
    for piece in text_pieces(w, paragraph, TextProps()):
        if isinstance(piece, Text):
            out.append(piece.text if piece.literal else _WHITESPACE.sub(" ", piece.text))
        elif piece.markdown == LINE_BREAK:
            out.append("\n")
        elif piece.markdown.startswith("[^"):  # a note's reference, as written in the code
            out.append(piece.markdown)
    return "".join(out)


def text_pieces(w: Writer, element: Element, props: TextProps) -> list[Piece]:
    pieces: list[Piece] = []
    # Each level: its children, the properties, the link, and whether it is inside an unknown
    # element (only the outermost unknown element is listed in the note).
    stack: list[tuple[Any, TextProps, str | None, bool]] = [
        (iter(element.children), props, None, False)
    ]
    while stack:
        items, current, link, unknown = stack[-1]
        item = next(items, None)
        if item is None:
            stack.pop()
            continue
        if isinstance(item, str):
            pieces.append(Text(item, current, link))
            continue
        tag = item.tag
        if tag in SPAN_LIKE:
            inner = w.state.styles.text_props(item.get("text:style-name"), current)
            if not inner.hidden:
                stack.append((iter(item.children), inner, link, unknown))
        elif tag == "text:a":
            stack.append((iter(item.children), current, link or item.get("xlink:href"), unknown))
        elif tag == "text:s":
            spaces = int_attribute(item.get("text:c"), 1, cap=MAX_SPACES)
            if spaces > 1 and not w.state.spend(spaces):  # one element, many characters
                spaces = 1
            pieces.append(Text(" " * spaces, current, link, literal=True))
        elif tag == "text:tab":
            pieces.append(Text("\t", current, link, literal=True))
        elif tag == "text:line-break":
            pieces.append(Raw(LINE_BREAK))
        elif tag == "text:note":
            pieces.append(Raw(note_reference(w, item)))
        elif tag == "office:annotation":
            w.state.counts.comments += 1
        elif tag == "text:hidden-text":
            if item.get("text:is-hidden") != "true":
                pieces.append(Text(item.get("text:string-value"), current, link))
        elif tag == "draw:frame":
            shown = frame_markdown(w, item)
            if shown:  # nothing to show (an empty formula): no piece between two spaces
                pieces.append(Raw(shown))
        elif tag == "draw:a":  # a linked frame: the frame matters, its link never does
            stack.append((iter(item.children), current, link, unknown))
        elif tag in DROPPED_INLINE:
            continue
        elif tag in FIELDS:
            if item.get("text:display") != "none":
                stack.append((iter(item.children), current, link, unknown))
        else:
            if not unknown:
                w.state.note_unknown(tag)
            stack.append((iter(item.children), current, link, True))  # its text is kept
    return pieces
