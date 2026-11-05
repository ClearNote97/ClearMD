"""Paragraphs: hidden ones, their properties and roles, and the paragraph and heading writers."""

from clearmd.backend.services.conversion.inline import LINE_BREAK, TextProps
from clearmd.backend.services.conversion.markdown_out import MARK, block, heading_text
from clearmd.backend.services.conversion.odt.styles import Role
from clearmd.backend.services.conversion.odt.writer.formulas import formula_markdown
from clearmd.backend.services.conversion.odt.writer.state import Writer
from clearmd.backend.services.conversion.odt.writer.vocab import DROPPED_BLOCKS
from clearmd.backend.services.conversion.xmltree import Element, int_attribute


def role_of(w: Writer, element: Element) -> Role | None:
    if element.tag != "text:p":
        return None
    return w.state.styles.role(element.get("text:style-name"))


def hidden(w: Writer, paragraph: Element) -> bool:
    """Hidden by a field in it, or by its style (``text:display="none"``)."""
    if w.state.styles.paragraph_props(paragraph.get("text:style-name")).hidden:
        return True
    return any(
        child.tag == "text:hidden-paragraph" and child.get("text:is-hidden") == "true"
        for child in paragraph.elements()
    )


def paragraph_props(w: Writer, paragraph: Element) -> TextProps:
    return w.state.styles.paragraph_props(paragraph.get("text:style-name"))


def paragraph_block(w: Writer, paragraph: Element) -> str:
    if hidden(w, paragraph):
        return ""
    style = paragraph.get("text:style-name")
    role = w.state.styles.role(style)
    if role in {Role.TITLE, Role.SUBTITLE}:
        text = w.inline(paragraph, TextProps()).replace(LINE_BREAK, " ")
        if not text:
            return ""
        return block(f"{MARK}# {text}" if role is Role.TITLE else f"{MARK}*{text}*")
    alone = sole_formula(paragraph)
    if alone is not None:  # a formula alone in its paragraph is display math
        shown = formula_markdown(w, alone, display=True)
        if shown is not None:
            return block(shown)
    text = w.inline(paragraph, paragraph_props(w, paragraph))
    return block(text) if text else ""


def heading_block(w: Writer, heading: Element) -> str:
    if hidden(w, heading):
        return ""
    # A heading's own bold is not emphasis; a line break in it never ends the heading.
    text = w.inline(heading, TextProps()).replace(LINE_BREAK, " ")
    if not text:
        return ""
    number = int_attribute(heading.get("text:outline-level"), w.state.top, cap=10)
    hashes = "#" * min(6, 2 + max(0, number - w.state.top))
    return block(f"{MARK}{hashes} {heading_text(text)}")


def own_paragraphs(w: Writer, element: Element) -> list[Element]:
    """The paragraphs and headings of ``element``, never those nested in them or in notes
    (they are part of their parent's text), each written once, in one pass; hidden sections,
    comments, deletions and generated content are left out, as ``write_block`` does."""
    found: list[Element] = []
    pending = list(reversed(list(element.elements())))
    while pending:
        child = pending.pop()
        tag = child.tag
        if tag in {"text:p", "text:h"}:
            found.append(child)
        elif tag == "text:tracked-changes":
            w.state.counts.changes += sum(1 for _ in child.elements("text:changed-region"))
        elif tag == "office:annotation":
            w.state.counts.comments += 1
        elif tag == "text:section" and child.get("text:display") == "none":
            continue
        elif tag not in DROPPED_BLOCKS and tag != "text:note":
            pending.extend(reversed(list(child.elements())))
    return found


def sole_formula(paragraph: Element) -> Element | None:
    """The formula object of a paragraph that holds nothing else (spaces aside)."""
    found: Element | None = None
    for child in paragraph.children:
        if isinstance(child, str):
            if child.strip():
                return None
            continue
        if child.tag in {"text:soft-page-break", "text:bookmark", "text:bookmark-start"}:
            continue
        formula = child.find("draw:object") if child.tag == "draw:frame" else None
        if formula is None or found is not None:
            return None
        found = formula
    return found
