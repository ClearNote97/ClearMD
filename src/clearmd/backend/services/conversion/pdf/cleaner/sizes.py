"""The body's size, each heading size's level, and what a heading looks like (008)."""

from collections import Counter

from clearmd.backend.services.conversion.pdf.cleaner.params import HEADING_RATIO, MAX_LEVEL
from clearmd.backend.services.conversion.pdf.model import Line

HEADING_TEXT_SHARE = 0.15  # a size holding more of the text than this is text, not headings
MAX_HEADING_CHARS = 150
MIN_LETTER_SHARE = 0.6  # a heading is words: a formula in a large font is not one


def size_key(size: float) -> float:
    return round(size * 2) / 2


def body_size(pages: list[list[Line]]) -> float:
    sizes: Counter[float] = Counter()
    for lines in pages:
        for line in lines:
            sizes[size_key(line.size)] += len(line.text)
    return sizes.most_common(1)[0][0] if sizes else 0.0


def heading_like(line: Line) -> bool:
    """Words, not too long, no sentence's end ("II. MARCO TEÓRICO." in capitals may end so)."""
    text = line.text
    visible = [char for char in text if not char.isspace()]
    letters = sum(char.isalpha() for char in visible)
    return (
        len(text) <= MAX_HEADING_CHARS
        and letters >= 3
        and letters >= MIN_LETTER_SHARE * len(visible)
        and (not text.endswith((".", ",", ";")) or (text.endswith(".") and text.isupper()))
        and "=" not in text
    )


def levels(pages: list[list[Line]], body: float) -> dict[float, int]:
    """Each heading size its level, the tallest first; a size that holds much of the text is a
    larger body, not headings."""
    if not body:
        return {}
    weight: Counter[float] = Counter()
    total = 0
    for lines in pages:
        for line in lines:
            weight[size_key(line.size)] += len(line.text)
            total += len(line.text)
    sizes = sorted(
        {
            size_key(line.size)
            for lines in pages
            for line in lines
            if line.size >= HEADING_RATIO * body
            and heading_like(line)
            and weight[size_key(line.size)] <= HEADING_TEXT_SHARE * total
        },
        reverse=True,
    )
    return {size: min(rank + 1, MAX_LEVEL) for rank, size in enumerate(sizes)}
