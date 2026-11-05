"""Lists: ordered, unordered and definition lists, their items nested up to ``MAX_LIST_LEVEL``."""

from clearmd.backend.services.conversion.html.writer.classify import is_block, next_significant
from clearmd.backend.services.conversion.html.writer.runs import inline_of
from clearmd.backend.services.conversion.html.writer.shapes import list_items, one_line
from clearmd.backend.services.conversion.html.writer.state import MAX_LIST_LEVEL, Writer
from clearmd.backend.services.conversion.inline import TextProps
from clearmd.backend.services.conversion.markdown_out import (
    MARK,
    indent,
    indent_all,
    neutralize,
    own_line,
    starts_tight,
    starts_with_fence,
)
from clearmd.backend.services.conversion.xmltree import Element


def list_block(w: Writer, element: Element, level: int) -> str:
    if element.get("rend") == "dl":
        return definitions_block(w, element)
    numbered = element.get("rend") == "ol"
    alternate = w.state.last_list == (numbered, False)
    delimiter, bullet = (")", "* ") if alternate else (".", "- ")
    lines: list[str] = []
    number = 1
    for item in list_items(element):
        content = list_item(w, item, level)
        if not content:
            continue
        marker = f"{number}{delimiter} " if numbered else bullet
        number += 1
        if not w.state.spend(len(marker) * (content.count("\n") + 1)):
            lines.append(MARK + marker + content.replace("\n", " "))
            continue
        if starts_with_fence(content):
            lines.append(MARK + marker.rstrip() + "\n" + indent_all(content, len(marker)))
        else:
            lines.append(MARK + marker + indent(content, len(marker)))
    w.state.last_list = (numbered, alternate)
    return "\n".join(lines)


def definitions_block(w: Writer, element: Element) -> str:
    """A definition list: each term a bold item, its definitions nested under it; their text
    neutralized like any other (a "# x" definition is never a heading)."""
    lines: list[str] = []
    for item in list_items(element):
        term = item.get("rend").startswith("dt")
        props = TextProps(bold=True) if term else TextProps()
        text = neutralize(one_line(inline_of(w, item.children, props)))
        if not text:
            continue
        lines.append(f"{MARK}- {text}" if term or not lines else f"  {MARK}- {text}")
    w.state.last_list = (False, False)
    return "\n".join(lines)


def list_item(w: Writer, item: Element, level: int) -> str:
    """An item's text, then its blocks (nested lists, paragraphs, quotes, code), neutralized
    at the item's own column and marked as ClearMD's (the enclosing levels only indent). A
    list nested deeper than ``MAX_LIST_LEVEL`` is written as its text."""
    from clearmd.backend.services.conversion.html.writer.dispatch import write_block

    parts: list[str] = []
    loose: list[Element | str] = []
    w.state.last_list = None

    def flush() -> None:
        if loose:
            text = inline_of(w, loose)
            if text:
                parts.append(text)
            loose.clear()
            w.state.last_list = None

    children = list(item.children)
    following = next_significant(children)
    for index, child in enumerate(children):
        if isinstance(child, Element) and child.tag == "list" and level >= MAX_LIST_LEVEL:
            w.state.note_unknown("list")
            loose.append(child)  # flattened: its items' text, in the item's text
        elif isinstance(child, Element) and child.tag == "list":
            flush()
            parts.append(list_block(w, child, level + 1))
        elif is_block(child, following[index], loose):
            assert isinstance(child, Element)
            flush()
            parts.append(write_block(w, child).strip("\n"))
        else:
            loose.append(child)
    flush()
    joined: list[str] = []
    for part in (p for p in parts if p):
        if joined:
            joined.append("\n" if starts_tight(part) else "\n\n")
        joined.append(part)
    text = neutralize("".join(joined), keep_marks=True)
    return "\n".join(own_line(line) for line in text.split("\n"))
