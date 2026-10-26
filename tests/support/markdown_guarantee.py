"""The output guarantee of ADR-0023/0024 as a check on parsed Markdown (converters' tests).

For hostile input, the Markdown must hold no raw HTML, no image, no link but the allowed ones, and
no block structure at the top level but paragraphs (and ClearMD's own code blocks).
"""

import re
from collections.abc import Iterator
from typing import Any

from markdown_it import MarkdownIt

PARSER = MarkdownIt("commonmark", {"html": True}).enable("table")
ALLOWED_BLOCKS = {"paragraph_open", "paragraph_close", "inline", "fence"}
_FOOTNOTE_DEFINITION = re.compile(r"(?m)^\[\^\d+\]: .*$")


def _tokens(markdown: str) -> Iterator[Any]:
    for token in PARSER.parse(markdown):
        yield token
        yield from token.children or []


def broken_promises(
    markdown: str,
    *,
    allowed_links: frozenset[str] = frozenset(),
    blocks: frozenset[str] = frozenset(),
) -> list[str]:
    """What breaks the guarantee in ``markdown`` (empty when it holds)."""
    found = []
    if re.search(r"(?<!\\)!\[\^\d+\]", markdown):
        found.append("image: a footnote reference after '!'")
    # A viewer with footnotes reads ClearMD's definitions as footnotes: taken out before parsing.
    markdown = _FOOTNOTE_DEFINITION.sub("", markdown)
    for token in _tokens(markdown):
        if token.type in {"html_inline", "html_block"}:
            found.append(f"html: {token.content!r}")
        elif token.type == "image":
            found.append(f"image: {token.attrs.get('src')!r}")
        elif token.type == "link_open" and token.attrs.get("href") not in allowed_links:
            found.append(f"link: {token.attrs.get('href')!r}")
    for token in PARSER.parse(markdown):
        allowed = ALLOWED_BLOCKS | blocks
        if token.nesting >= 0 and token.level == 0 and token.type not in allowed:
            found.append(f"block: {token.type}")
    return [f"{problem} in {markdown!r}" for problem in found]
