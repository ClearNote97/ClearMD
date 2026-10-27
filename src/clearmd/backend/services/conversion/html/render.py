"""trafilatura's XML → Markdown, written by ClearMD (ADR-0025): the subset of spec 004.

trafilatura finds the article; this renderer writes it with the same guarantee as ClearMD's other
converters: every text through ``inline`` and ``markdown_out`` (escaped, emphasis Markdown can
hold, links by the rules of ADR-0023), ClearMD's own block lines marked and the rest neutralized,
images as placeholders, a growth budget. Standard library only; blocks nested deeper than
``MAX_NESTING``, and lists deeper than ``MAX_LIST_LEVEL``, are written as their text.
"""

import re
from dataclasses import replace
from typing import Any

from clearmd.backend.schemas.notes import ConversionNote, NoteItem, NoteKind
from clearmd.backend.services.conversion.inline import (
    IMAGE_WORD,
    LINE_BREAK,
    InlineWriter,
    Piece,
    Raw,
    Text,
    TextProps,
)
from clearmd.backend.services.conversion.markdown_out import (
    MARK,
    block,
    escape_text,
    fence_for,
    heading_text,
    indent,
    indent_all,
    neutralize,
    outside_code,
    own_line,
    starts_tight,
    starts_with_fence,
    tidy,
)
from clearmd.backend.services.conversion.xmltree import Element, int_attribute

GROWTH_FACTOR = 4
GROWTH_EXTRA = 1024**2
MAX_NESTING = 32  # quotes, tables and divisions inside each other
MAX_LIST_LEVEL = 10  # a list nested deeper is written as its text
MAX_CELLS = 100_000
MAX_UNKNOWN = 1000
# hi@rend → the property it sets.
HI: dict[str, dict[str, Any]] = {
    "#b": {"bold": True}, "#i": {"italic": True}, "#u": {"underline": True},
    "#t": {"mono": True}, "#sup": {"position": "super"}, "#sub": {"position": "sub"},
}  # fmt: skip
BLOCKS = frozenset({"head", "p", "list", "quote", "code", "table", "div", "ab"})


class ArticleRenderer:
    def __init__(self, *, language: str, source_size: int) -> None:
        self._image_word = IMAGE_WORD.get(language.split("-")[0].lower(), "Image")
        self._room = GROWTH_FACTOR * source_size + GROWTH_EXTRA
        self._writer = InlineWriter(self._spend)
        self._top = 1
        self._depth = 0
        self._last_list: tuple[bool, bool] | None = None  # (numbered, other markers)
        self._images = 0
        self._tables_simplified = 0
        self._unknown: dict[str, None] = {}

    # --- Document --------------------------------------------------------------------------

    def document(self, main: Element, *, title: str = "") -> str:
        """``main``: the article's tree. Its first ``h1``, wherever it is, is the title
        (``# Title``); without one, ``title`` (the page's ``<title>``). Other headings start at
        ``##``."""
        heading, parent = _first_h1(main)
        written = ""
        if heading is not None and parent is not None and heading.text().strip():
            parent.children.remove(heading)  # a logo (only an image) is not the title
            written = _one_line(self._inline_of(heading.children))
        if not written:
            written = escape_text(" ".join(title.split()))
        levels = [
            int_attribute(head.get("rend")[1:], 2, cap=6)
            for head in main.walk()
            if head.tag == "head" and head.get("rend")
        ]
        self._top = min(levels, default=2)
        parts = [block(f"{MARK}# {heading_text(written)}")] if written else []
        parts.append(self.blocks(list(main.children)))
        return neutralize(tidy("".join(parts)))

    def blocks(self, children: list[Element | str]) -> str:
        parts: list[str] = []
        loose: list[Element | str] = []  # text and inline elements between blocks: a paragraph

        def flush() -> None:
            if loose:
                text = self._inline_of(loose)
                if text:
                    parts.append(block(text))
                    self._last_list = None
                loose.clear()

        following = _next_significant(children)
        for index, child in enumerate(children):
            if _is_block(child, following[index], loose):
                assert isinstance(child, Element)
                flush()
                written = self._block(child)
                if child.tag != "list" and written.strip():
                    self._last_list = None
                parts.append(written)
            else:
                loose.append(child)
        flush()
        return "".join(parts)

    def _block(self, element: Element) -> str:
        tag = element.tag
        if self._depth >= MAX_NESTING:
            self._note_unknown(tag)
            text = escape_text(" ".join(element.text().split()))
            return block(text) if text else ""
        self._depth += 1
        try:
            if tag == "head":
                return self._heading(element)
            if tag == "p":
                text = self._inline_of(element.children)
                return block(text) if text else ""
            if tag == "list":
                return block(self._list(element, 1))
            if tag == "quote":
                return self._quote(element)
            if tag == "code":
                return self._code(element)
            if tag == "table":
                return self._table(element)
            return self.blocks(list(element.children))  # div, ab: their content
        finally:
            self._depth -= 1

    def _heading(self, element: Element) -> str:
        if not element.get("rend"):  # a heading without a level (a summary): bold, not a heading
            text = _one_line(self._inline_of(element.children, TextProps(bold=True)))
            return block(text) if text else ""
        text = _one_line(self._inline_of(element.children))
        if not text:
            return ""
        level = int_attribute(element.get("rend")[1:], self._top, cap=6)
        hashes = "#" * min(6, 2 + max(0, level - self._top))
        return block(f"{MARK}{hashes} {heading_text(text)}")

    def _quote(self, element: Element) -> str:
        inner = self.blocks(list(element.children)).strip("\n")
        inner = outside_code(inner, lambda part: re.sub(r"\n{3,}", "\n\n", part))
        if not inner:
            return ""
        lines = neutralize(inner, keep_marks=True).split("\n")
        quoted = (f"{MARK}> {own_line(line)}" if line else f"{MARK}>" for line in lines)
        return block("\n".join(quoted))

    def _code(self, element: Element) -> str:
        code = _code_text(element).strip("\n")
        if not code.strip() or not self._spend(len(code)):
            return ""
        fence = fence_for(code)
        return block(f"{MARK}{fence}\n{code}\n{MARK}{fence}")

    def _list(self, element: Element, level: int) -> str:
        if element.get("rend") == "dl":
            return self._definitions(element)
        numbered = element.get("rend") == "ol"
        alternate = self._last_list == (numbered, False)
        delimiter, bullet = (")", "* ") if alternate else (".", "- ")
        lines: list[str] = []
        number = 1
        for item in _items(element):
            content = self._item(item, level)
            if not content:
                continue
            marker = f"{number}{delimiter} " if numbered else bullet
            number += 1
            if not self._spend(len(marker) * (content.count("\n") + 1)):
                lines.append(MARK + marker + content.replace("\n", " "))
                continue
            if starts_with_fence(content):
                lines.append(MARK + marker.rstrip() + "\n" + indent_all(content, len(marker)))
            else:
                lines.append(MARK + marker + indent(content, len(marker)))
        self._last_list = (numbered, alternate)
        return "\n".join(lines)

    def _definitions(self, element: Element) -> str:
        """A definition list: each term a bold item, its definitions nested under it; their text
        neutralized like any other (a "# x" definition is never a heading)."""
        lines: list[str] = []
        for item in _items(element):
            term = item.get("rend").startswith("dt")
            props = TextProps(bold=True) if term else TextProps()
            text = neutralize(_one_line(self._inline_of(item.children, props)))
            if not text:
                continue
            lines.append(f"{MARK}- {text}" if term or not lines else f"  {MARK}- {text}")
        self._last_list = (False, False)
        return "\n".join(lines)

    def _item(self, item: Element, level: int) -> str:
        """An item's text, then its blocks (nested lists, paragraphs, quotes, code), neutralized
        at the item's own column and marked as ClearMD's (the enclosing levels only indent). A
        list nested deeper than ``MAX_LIST_LEVEL`` is written as its text."""
        parts: list[str] = []
        loose: list[Element | str] = []
        self._last_list = None

        def flush() -> None:
            if loose:
                text = self._inline_of(loose)
                if text:
                    parts.append(text)
                loose.clear()
                self._last_list = None

        children = list(item.children)
        following = _next_significant(children)
        for index, child in enumerate(children):
            if isinstance(child, Element) and child.tag == "list" and level >= MAX_LIST_LEVEL:
                self._note_unknown("list")
                loose.append(child)  # flattened: its items' text, in the item's text
            elif isinstance(child, Element) and child.tag == "list":
                flush()
                parts.append(self._list(child, level + 1))
            elif _is_block(child, following[index], loose):
                assert isinstance(child, Element)
                flush()
                parts.append(self._block(child).strip("\n"))
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

    def _table(self, element: Element) -> str:
        grid: list[list[str]] = []
        plain: list[str] = []  # the cells' text, for a table the budget cannot pay for
        overflow: list[str] = []  # the text of the rows past MAX_CELLS
        cells = 0
        for row in _rows(element):
            texts = [" ".join(cell.text().split()) for cell in _cells(row)]
            if cells + len(texts) > MAX_CELLS:
                if not overflow:
                    self._note_unknown("table")  # its text follows the table, as a paragraph
                overflow.append(" ".join(text for text in texts if text))
                cells += len(texts)
                continue
            line = [
                _one_line(self._inline_of(cell.children)).replace("|", "\\|")
                for cell in _cells(row)
            ]
            plain.extend(texts)
            cells += len(line)
            while line and not line[-1]:
                line.pop()
            if line:
                grid.append(line)
        after = block(escape_text(" ".join(t for t in overflow if t))) if overflow else ""
        if not grid:
            return after
        width = max(len(line) for line in grid)
        caption = ""
        if len(grid) > 1 and len(grid[0]) == 1 and width > 1:  # a caption, not the header
            caption = block(grid.pop(0)[0])
        if not self._spend(8 * width + sum(3 * (width - len(line)) for line in grid)):
            return block(escape_text(" ".join(text for text in plain if text))) + after
        rows = [MARK + "| " + " | ".join(line + [""] * (width - len(line))) + " |" for line in grid]
        rows.insert(1, MARK + "|" + "---|" * width)
        return caption + block("\n".join(rows)) + after

    # --- Inline ------------------------------------------------------------------------------

    def _inline_of(self, nodes: list[Element | str], props: TextProps | None = None) -> str:
        pieces = self._pieces(nodes, props or TextProps())
        return self._writer.write(self._writer.normalize(pieces))

    def _pieces(self, nodes: list[Element | str], props: TextProps) -> list[Piece]:
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
                stack.append((iter(item.children), _with(current, changes), link))
            elif tag == "del":
                stack.append((iter(item.children), _with(current, {"strike": True}), link))
            elif tag == "ref":
                stack.append((iter(item.children), current, link or item.get("target")))
            elif tag == "lb":
                pieces.append(Raw(LINE_BREAK))
            elif tag == "graphic":
                # Text the emphasis checks see: next to a word in italics it never shows "**".
                pieces.append(Text(self._image(item), _with(current, {"italic": True}), link))
            elif tag == "code":
                stack.append((iter(item.children), _with(current, {"mono": True}), link))
            elif tag in {"quote", "q"}:  # a short quotation inside a sentence
                stack.append((iter(item.children), current, link))
            else:
                if tag not in BLOCKS and tag not in {"item", "row", "cell"}:
                    self._note_unknown(tag)
                pieces.append(Text(" ", current, link))  # a block inside text: kept, apart
                stack.append((iter(item.children), current, link))
        return pieces

    def _image(self, graphic: Element) -> str:
        self._images += 1
        label = " ".join((graphic.get("alt") or graphic.get("title")).split())
        return f"{self._image_word}: {label}" if label else self._image_word

    # --- Budget and notes --------------------------------------------------------------------

    def _spend(self, size: int) -> bool:
        if size > self._room:
            self._room = 0
            return False
        self._room -= size
        return True

    def _note_unknown(self, tag: str) -> None:
        if tag in self._unknown or len(self._unknown) < MAX_UNKNOWN:
            self._unknown[tag] = None

    def notes(self) -> tuple[ConversionNote, ...]:
        found: list[ConversionNote] = []
        if self._images:
            found.append(
                ConversionNote(NoteKind.IMAGES_NOT_DOWNLOADED, (NoteItem(str(self._images)),))
            )
        if self._writer.dropped:
            count = NoteItem(str(self._writer.dropped))
            found.append(ConversionNote(NoteKind.FORMATTING_DROPPED, (count,)))
        if self._tables_simplified:
            count = NoteItem(str(self._tables_simplified))
            found.append(ConversionNote(NoteKind.TABLE_SIMPLIFIED, (count,)))
        if self._unknown:
            items = tuple(NoteItem(tag) for tag in self._unknown)
            found.append(ConversionNote(NoteKind.ELEMENTS_SIMPLIFIED, items))
        return tuple(found)


def _with(props: TextProps, changes: dict[str, Any]) -> TextProps:
    return replace(props, **changes)


def _first_h1(main: Element) -> tuple[Element | None, Element | None]:
    """The first ``head rend="h1"`` with text under ``main`` and its parent (document order)."""
    pending: list[tuple[Element, Element]] = [
        (child, main) for child in reversed(list(main.elements()))
    ]
    while pending:
        element, parent = pending.pop()
        if element.tag == "head" and element.get("rend") == "h1" and element.text().strip():
            return element, parent  # the first with text (a logo, only an image, is not)
        pending.extend((child, element) for child in reversed(list(element.elements())))
    return None, None


def _is_block(
    child: Element | str, following: Element | str | None, loose: list[Element | str]
) -> bool:
    """Whether ``child`` is written as a block. trafilatura writes inline code and short
    quotations (``<q>``) with the same tags as blocks: one with text or inline elements around it
    is inline, unless it holds lines (a code block) or blocks. The whole page's ``<pre>`` and
    ``<blockquote>`` are always blocks."""
    if not isinstance(child, Element) or child.tag not in BLOCKS:
        return False
    if child.tag not in {"code", "quote"} or child.get("rend") in {"pre", "block"}:
        return True
    if child.tag == "code" and (
        child.find("code") is not None
        or child.find("lb") is not None
        or "\n" in child.text().strip("\n")
    ):
        return True
    if child.tag == "quote" and any(c.tag in BLOCKS for c in child.elements()):
        return True
    before = any(not isinstance(node, str) or node.strip() for node in loose)
    after = isinstance(following, str) or (
        isinstance(following, Element)
        and (following.tag not in BLOCKS or following.tag in {"code", "quote"})
        and following.get("rend") not in {"pre", "block"}
    )
    return not (before or after)


def _next_significant(children: list[Element | str]) -> list[Element | str | None]:
    """For each position, the next sibling that is an element or non-blank text (one pass)."""
    found: list[Element | str | None] = [None] * len(children)
    following: Element | str | None = None
    for index in range(len(children) - 1, -1, -1):
        found[index] = following
        node = children[index]
        if not isinstance(node, str) or node.strip():
            following = node
    return found


def _items(element: Element) -> list[Element]:
    """A list's items, through what wraps them (``<dl><div><dt>``, ``<ul><a><li>``); text or an
    element with no item inside becomes an item of its own, never lost."""
    found: list[Element] = []
    pending: list[Element | str] = list(reversed(element.children))
    while pending:
        node = pending.pop()
        if isinstance(node, str):
            if node.strip():
                found.append(Element("item", {}, [node]))
        elif node.tag == "item":
            found.append(node)
        elif node.tag != "list" and node.find("item") is not None:
            pending.extend(reversed(node.children))  # a wrapper: its items, in order
        else:
            found.append(Element("item", {}, [node]))  # a nested list, a paragraph…
    return found


def _rows(table: Element) -> list[Element]:
    """A table's rows, through what wraps them (``<table><form><tr>``); a bare cell or text
    becomes a row of its own. Nested tables are their cells' content, not rows here."""
    found: list[Element] = []
    pending: list[Element | str] = list(reversed(table.children))
    while pending:
        node = pending.pop()
        if isinstance(node, str):
            if node.strip():
                found.append(Element("row", {}, [Element("cell", {}, [node])]))
        elif node.tag == "row":
            found.append(node)
        elif node.tag == "cell":
            found.append(Element("row", {}, [node]))
        elif node.tag == "table":  # a table inside the table, outside a cell: its text, apart
            found.append(Element("row", {}, [Element("cell", {}, [node])]))
        else:
            pending.extend(reversed(node.children))
    return found


def _cells(row: Element) -> list[Element]:
    """A row's cells; text beside them becomes a cell of its own."""
    cells = []
    for node in row.children:
        if isinstance(node, Element) and node.tag == "cell":
            cells.append(node)
        elif isinstance(node, str) and node.strip() or isinstance(node, Element):
            cells.append(Element("cell", {}, [node]))
    return cells


def _code_text(element: Element) -> str:
    """A code block's text as written, a line break for each ``lb``."""
    out: list[str] = []
    pending: list[Element | str] = [element]
    while pending:
        node = pending.pop()
        if isinstance(node, str):
            out.append(node)
        elif node.tag == "lb":
            out.append("\n")
        else:
            pending.extend(reversed(node.children))
    return "".join(out)


def _one_line(text: str) -> str:
    """Text whose hard line breaks become one space (a heading, a cell, the title)."""
    return re.sub(r" *  \n *", " ", text)
