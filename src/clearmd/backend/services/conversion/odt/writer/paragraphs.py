"""Paragraphs: what a paragraph holds, and the writers of paragraphs and headings."""

from clearmd.backend.services.conversion.xmltree import Element


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
