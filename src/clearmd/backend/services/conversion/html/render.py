"""trafilatura's XML → Markdown, written by ClearMD (ADR-0025): the subset of spec 004.

trafilatura finds the article; this renderer writes it with the same guarantee as ClearMD's other
converters: every text through ``inline`` and ``markdown_out`` (escaped, emphasis Markdown can
hold, links by the rules of ADR-0023), ClearMD's own block lines marked and the rest neutralized,
images as placeholders, a growth budget. Standard library only; blocks nested deeper than
``MAX_NESTING``, and lists deeper than ``MAX_LIST_LEVEL``, are written as their text.

``ArticleRenderer`` keeps the recursive entry points (``document``, ``blocks``); the writers in
``html/writer/`` are plain functions that take it, so a level of nesting costs the same Python
frames as when they were methods.
"""

from clearmd.backend.schemas.notes import ConversionNote
from clearmd.backend.services.conversion.html.writer.classify import (
    first_h1,
    is_block,
    next_significant,
)
from clearmd.backend.services.conversion.html.writer.dispatch import write_block
from clearmd.backend.services.conversion.html.writer.runs import inline_of
from clearmd.backend.services.conversion.html.writer.shapes import one_line
from clearmd.backend.services.conversion.html.writer.state import ArticleState, collect_notes
from clearmd.backend.services.conversion.markdown_out import (
    MARK,
    block,
    escape_text,
    heading_text,
    neutralize,
    tidy,
)
from clearmd.backend.services.conversion.xmltree import Element, int_attribute


class ArticleRenderer:
    """Trafilatura elements → Markdown. What a run accumulates lives in ``state``."""

    def __init__(self, *, language: str, source_size: int) -> None:
        self.state = ArticleState(language=language, source_size=source_size)

    # --- Entry points -------------------------------------------------------------------------

    def document(self, main: Element, *, title: str = "") -> str:
        """``main``: the article's tree. Its first ``h1``, wherever it is, is the title
        (``# Title``); without one, ``title`` (the page's ``<title>``). Other headings start at
        ``##``."""
        heading, parent = first_h1(main)
        written = ""
        if heading is not None and parent is not None and heading.text().strip():
            parent.children.remove(heading)  # a logo (only an image) is not the title
            written = one_line(inline_of(self, heading.children))
        if not written:
            written = escape_text(" ".join(title.split()))
        levels = [
            int_attribute(head.get("rend")[1:], 2, cap=6)
            for head in main.walk()
            if head.tag == "head" and head.get("rend")
        ]
        self.state.top = min(levels, default=2)
        parts = [block(f"{MARK}# {heading_text(written)}")] if written else []
        parts.append(self.blocks(list(main.children)))
        return neutralize(tidy("".join(parts)))

    def blocks(self, children: list[Element | str]) -> str:
        parts: list[str] = []
        loose: list[Element | str] = []  # text and inline elements between blocks: a paragraph

        def flush() -> None:
            if loose:
                text = inline_of(self, loose)
                if text:
                    parts.append(block(text))
                    self.state.last_list = None
                loose.clear()

        following = next_significant(children)
        for index, child in enumerate(children):
            if is_block(child, following[index], loose):
                assert isinstance(child, Element)
                flush()
                written = write_block(self, child)
                if child.tag != "list" and written.strip():
                    self.state.last_list = None
                parts.append(written)
            else:
                loose.append(child)
        flush()
        return "".join(parts)

    def notes(self) -> tuple[ConversionNote, ...]:
        """The notes this run earned."""
        return collect_notes(self)
