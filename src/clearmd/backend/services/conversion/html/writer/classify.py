"""Which children of an element are blocks, and where the article's title is."""

from clearmd.backend.services.conversion.html.writer.state import BLOCKS
from clearmd.backend.services.conversion.xmltree import Element


def first_h1(main: Element) -> tuple[Element | None, Element | None]:
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


def is_block(
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


def next_significant(children: list[Element | str]) -> list[Element | str | None]:
    """For each position, the next sibling that is an element or non-blank text (one pass)."""
    found: list[Element | str | None] = [None] * len(children)
    following: Element | str | None = None
    for index in range(len(children) - 1, -1, -1):
        found[index] = following
        node = children[index]
        if not isinstance(node, str) or node.strip():
            following = node
    return found
