"""A page's footnotes: the small lines under its text, and the queue that holds them (008)."""

import re

from clearmd.backend.services.conversion.markdown_out import escape_text
from clearmd.backend.services.conversion.pdf.cleaner.joining import joined
from clearmd.backend.services.conversion.pdf.cleaner.render import is_block
from clearmd.backend.services.conversion.pdf.model import Line

FOOTNOTE_RATIO = 0.9  # the small lines at the foot of a page, under its text: its footnotes
NOTE_START = re.compile(r"(?:\d{1,3}|[⁰¹²³⁴⁵⁶⁷⁸⁹]{1,3}|[*†‡§])\s*\S")  # "¹" too (014)


def split_footnotes(lines: list[Line], body: float) -> tuple[list[Line], list[Line]]:
    """The page's text, and the small lines under it (its footnotes)."""
    start = len(lines)
    while (
        start > 0
        and not is_block(lines[start - 1])
        and lines[start - 1].size < FOOTNOTE_RATIO * body
    ):
        start -= 1
    if start == 0 or start == len(lines) or not body:
        return lines, []
    return lines[:start], lines[start:]


class FootnoteQueue:
    """Footnotes held, one block each, until the paragraph they cut ends."""

    def __init__(self) -> None:
        self.held: list[str] = []  # footnotes, written once the paragraph they cut ends

    def hold(self, notes: list[Line]) -> None:
        """A page's footnotes: one block each, after the paragraph the page break cut."""
        parts: list[str] = []
        for line in notes:
            if parts and NOTE_START.match(line.text):
                self.held.append(escape_text(joined(parts)))
                parts = []
            parts.append(line.text)
        if parts:
            self.held.append(escape_text(joined(parts)))

    def release(self, blocks: list[str]) -> None:
        """The held footnotes join the blocks, after what is written."""
        blocks.extend(self.held)
        self.held = []
