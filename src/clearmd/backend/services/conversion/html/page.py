"""The whole page, written by ClearMD, when article mode finds no article (ADR-0025).

The page is parsed by lxml's HTML parser (never fetching anything) and its elements are mapped to
the same tree trafilatura gives for an article, so ``render`` writes it with the same guarantee:
headings, paragraphs, lists, quotes, code, tables, links, emphasis, images as placeholders.
What is never content (scripts, styles, frames, embedded objects, form controls) is dropped; any
other element keeps its text. Walked without recursion, under the XML reader's limits.
"""

import re
from typing import Any

from lxml import html as lxml_html  # type: ignore[import-untyped]  # trafilatura's own parser

from clearmd.backend.services.conversion.xmltree import Element, XmlLimits

_MARK = ""  # ClearMD's mark for its own block lines (markdown_out.MARK)
_DECLARATION = re.compile(r"^\s*<\?xml[^>]*\?>", re.IGNORECASE)
DROPPED = frozenset(
    {
        "script", "style", "noscript", "template", "iframe", "frame", "frameset", "object",
        "embed", "svg", "math", "canvas", "audio", "video", "source", "track", "map", "head",
        "input", "select", "option", "textarea", "button", "meta", "link",
    }
)  # fmt: skip
HEADINGS = {f"h{n}": f"h{n}" for n in range(1, 7)}
EMPHASIS = {
    **dict.fromkeys(("b", "strong"), "#b"),
    **dict.fromkeys(("i", "em", "cite", "dfn", "var"), "#i"),
    **dict.fromkeys(("u", "ins"), "#u"),
    **dict.fromkeys(("code", "kbd", "samp", "tt"), "#t"),
    "sup": "#sup",
    "sub": "#sub",
}
CONTAINERS = frozenset(
    {
        "body", "div", "section", "article", "main", "header", "footer", "nav", "aside",
        "figure", "figcaption", "address", "details", "summary", "center", "form", "fieldset",
        "legend", "hgroup", "caption",
    }
)  # fmt: skip


def page_tree(page: str) -> Element | None:
    """The page as an article-like tree (``body`` → ``head``, ``p``, ``list``…); ``None`` when
    lxml finds nothing."""
    try:
        document = lxml_html.document_fromstring(_DECLARATION.sub("", page))
    except Exception:  # noqa: BLE001 -- lxml refuses it (empty, binary): nothing to write
        return None
    body = document.find("body")
    return _convert(body if body is not None else document)


def _mapped(node: Any) -> Element | None:
    """The element ``node`` becomes; ``None`` for one whose children go straight to its parent
    (an inline element with no meaning of its own)."""
    tag = str(node.tag).lower()
    if tag in HEADINGS:
        return Element("head", {"rend": HEADINGS[tag]})
    if tag in EMPHASIS:
        return Element("hi", {"rend": EMPHASIS[tag]})
    if tag in {"s", "strike", "del"}:
        return Element("del", {"rend": "overstrike"})
    if tag == "a":
        return Element("ref", {"target": str(node.get("href") or "")})
    if tag == "br":
        return Element("lb")
    if tag == "img":
        alt, title = str(node.get("alt") or ""), str(node.get("title") or "")
        return Element("graphic", {"alt": alt, "title": title})
    if tag in {"ul", "menu"}:
        return Element("list", {"rend": "ul"})
    if tag == "ol":
        return Element("list", {"rend": "ol"})
    if tag == "dl":
        return Element("list", {"rend": "dl"})
    if tag == "li":
        return Element("item")
    if tag in {"dt", "dd"}:
        return Element("item", {"rend": f"{tag}-1"})
    if tag in {"blockquote", "q"}:
        return Element("quote")
    if tag == "pre":
        return Element("code")
    if tag == "table":
        return Element("table")
    if tag == "tr":
        return Element("row")
    if tag in {"td", "th"}:
        return Element("cell", {"role": "head"} if tag == "th" else {})
    if tag == "p":
        return Element("p")
    if tag in CONTAINERS:
        return Element("div")
    return None  # span, small, mark, abbr, time, label, thead, tbody…: their content only


def _convert(root: Any) -> Element | None:
    limits = XmlLimits()
    budget = {"elements": 0, "characters": 0}

    def clean(text: str | None) -> str:
        text = (text or "").replace(_MARK, "").replace("\r\n", "\n").replace("\r", "\n")
        budget["characters"] += len(text)
        return text

    top = Element("body")
    # (node, parent, inside a <pre>), or (None, parent, text): a tail, written after the
    # subtree of the element it follows (it is pushed before that subtree).
    pending: list[tuple[Any, Element, Any]] = [(root, top, False)]
    while pending:
        node, parent, extra = pending.pop()
        if node is None:
            parent.children.append(clean(extra))
            continue
        if node is not root and node.tail:
            pending.append((None, parent, node.tail))
        tag = node.tag
        if not isinstance(tag, str) or tag.lower() in DROPPED:  # a comment, a script…
            continue
        budget["elements"] += 1
        if budget["elements"] > limits.max_elements or budget["characters"] > limits.max_characters:
            return None
        name = tag.lower()
        in_pre = bool(extra)
        element = None if node is root or (in_pre and name == "code") else _mapped(node)
        target = element if element is not None else parent
        if element is not None:
            parent.children.append(element)
        if node.text:
            target.children.append(clean(node.text))
        for child in reversed(list(node)):
            pending.append((child, target, in_pre or name == "pre"))
    return top
