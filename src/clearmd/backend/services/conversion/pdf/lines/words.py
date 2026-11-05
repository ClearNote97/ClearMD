"""A word's box in its frame: the page turned so the word reads upright (feature 013)."""

from clearmd.backend.services.conversion.pdf.model import (
    CLOCKWISE,
    COUNTERCLOCKWISE,
    UPRIGHT,
    Chars,
)
from clearmd.backend.services.conversion.pdf.tables import Word


def build_word(text: str, chars: Chars, indices: list[int], turn: int) -> Word:
    """A word's box in its frame: the page turned so its text reads upright (a clockwise turn
    takes the page's top to the frame's left)."""
    first, last = indices[0], indices[-1] + 1
    if last - first == len(indices):  # one run of characters, as nearly always: slices (fast)
        left, right = min(chars.lefts[first:last]), max(chars.rights[first:last])
        bottom, top = min(chars.bottoms[first:last]), max(chars.tops[first:last])
        if turn == UPRIGHT:
            return Word(text, left, right, bottom, top, max(chars.sizes[first:last]))
    else:
        left = min(chars.lefts[i] for i in indices)
        right = max(chars.rights[i] for i in indices)
        bottom = min(chars.bottoms[i] for i in indices)
        top = max(chars.tops[i] for i in indices)
    if turn == CLOCKWISE:
        return Word(text, -top, -bottom, left, right, max(width(chars, i) for i in indices))
    if turn == COUNTERCLOCKWISE:
        return Word(text, bottom, top, -right, -left, max(width(chars, i) for i in indices))
    return Word(text, left, right, bottom, top, max(chars.sizes[i] for i in indices))


def width(chars: Chars, index: int) -> float:
    return max(chars.rights[index] - chars.lefts[index], 0.0)
