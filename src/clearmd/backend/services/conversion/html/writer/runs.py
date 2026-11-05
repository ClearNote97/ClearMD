"""Inline runs: the properties an inline element sets on its text, and the runs of a paragraph."""

from dataclasses import replace
from typing import Any

from clearmd.backend.services.conversion.html.writer.state import BLOCKS, HI, Writer
from clearmd.backend.services.conversion.inline import LINE_BREAK, Piece, Raw, Text, TextProps
from clearmd.backend.services.conversion.xmltree import Element


def with_props(props: TextProps, changes: dict[str, Any]) -> TextProps:
    return replace(props, **changes)


def inline_of(w: Writer, nodes: list[Element | str], props: TextProps | None = None) -> str:
    pieces = text_pieces(w, nodes, props or TextProps())
    return w.state.writer.write(w.state.writer.normalize(pieces))


def text_pieces(w: Writer, nodes: list[Element | str], props: TextProps) -> list[Piece]:
    pieces: list[Piece] = []
    stack: list[tuple[Any, TextProps, str | None]] = [(iter(nodes), props, None)]
    while stack:
        items, current, link = stack[-1]
        item = next(items, None)
        if item is None:
            stack.pop()
            continue
        if isinstance(item, str):
            pieces.append(Text(item, current, link))
            continue
        tag = item.tag
        if tag == "hi":
            changes = HI.get(item.get("rend"), {})
            stack.append((iter(item.children), with_props(current, changes), link))
        elif tag == "del":
            stack.append((iter(item.children), with_props(current, {"strike": True}), link))
        elif tag == "ref":
            stack.append((iter(item.children), current, link or item.get("target")))
        elif tag == "lb":
            pieces.append(Raw(LINE_BREAK))
        elif tag == "graphic":
            # Text the emphasis checks see: next to a word in italics it never shows "**".
            pieces.append(Text(image_text(w, item), with_props(current, {"italic": True}), link))
        elif tag == "code":
            stack.append((iter(item.children), with_props(current, {"mono": True}), link))
        elif tag in {"quote", "q"}:  # a short quotation inside a sentence
            stack.append((iter(item.children), current, link))
        else:
            if tag not in BLOCKS and tag not in {"item", "row", "cell"}:
                w.state.note_unknown(tag)
            pieces.append(Text(" ", current, link))  # a block inside text: kept, apart
            stack.append((iter(item.children), current, link))
    return pieces


def image_text(w: Writer, graphic: Element) -> str:
    w.state.images += 1
    label = " ".join((graphic.get("alt") or graphic.get("title")).split())
    return f"{w.state.image_word}: {label}" if label else w.state.image_word
