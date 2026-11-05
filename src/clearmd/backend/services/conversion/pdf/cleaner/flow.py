"""The block being written (its kind, its lines, the line before) and what is measured on it.

Alone, so the heading, item and buffer modules all type on it: none of them owns the state.
"""

from dataclasses import dataclass, field

from clearmd.backend.services.conversion.pdf.cleaner.params import PARAGRAPH_GAP, SENTENCE_END
from clearmd.backend.services.conversion.pdf.model import Line


@dataclass
class Flow:
    """The state of the block being built: kind, lines so far, the line before it, the heading's
    level and the page's typical line length."""

    kind: str = ""  # "", "heading", "item", "text"
    parts: list[str] = field(default_factory=list)
    last: Line | None = None
    level: int = 0
    typical: float = 80.0  # a full line's length on this page, in characters
    grown: bool = False  # the paragraph started as a heading: a larger font, too long for one
    numbered: bool = False  # the heading came from a bold number, not from its size


def sentence_ended(flow: Flow) -> bool:
    """The block so far ends a sentence."""
    return bool(flow.parts) and bool(SENTENCE_END.search(flow.parts[-1]))


def paragraph_ended(flow: Flow) -> bool:
    """The previous line ended a sentence and the next one starts a new one with a capital:
    a paragraph ends there only if that line was short (the rest of it was left blank)."""
    last = flow.last
    return last is not None and bool(SENTENCE_END.search(last.text)) and is_short(flow, last)


def is_short(flow: Flow, line: Line) -> bool:
    """The line is much shorter than a full one on this page."""
    return len(line.text) < 0.6 * flow.typical


def set_typical(flow: Flow, lines: list[Line]) -> None:
    """A full line's length on this page: the third quartile of the lines' lengths."""
    lengths = sorted(len(line.text) for line in lines)
    flow.typical = float(lengths[len(lengths) * 3 // 4]) if lengths else 80.0


def has_gap(flow: Flow, line: Line) -> bool:
    """A blank between the line before and this one, or a new column."""
    last = flow.last
    if last is None:
        return False
    height = max(min(last.size, line.size), 1.0)
    blank = last.bottom - line.top
    return blank > PARAGRAPH_GAP * height or line.top > last.top + height  # or a new column
