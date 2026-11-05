"""Where a line PDFium ends goes on, and where a sideways row starts another (feature 013, 014)."""

from clearmd.backend.services.conversion.pdf.lines.words import width
from clearmd.backend.services.conversion.pdf.model import (
    ASLANT,
    CLOCKWISE,
    COUNTERCLOCKWISE,
    UPRIGHT,
    Chars,
)

LOOK_AHEAD = 4  # characters looked at past a line's end (its carriage return, a space)
ROW_OVERLAP = 0.5  # of the shorter box: two characters this much level are on one row
SCRIPT_GAP_EMS = 0.5  # a script starts at most this far from what it is set on
NEW_ROW_SHARE = 0.5  # of a sideways letter's height: a character this far across is on another row


def goes_on(chars: Chars, last: int, index: int, extent: list[float]) -> bool:
    """Whether a line PDFium ends goes on in the next one: the next character stands on the same
    row, right after the last (a subscript PDFium put on a line of its own: "Rᴺ" then "₊")."""
    following = next(
        (i for i in range(index + 1, min(index + LOOK_AHEAD, len(chars.codes)))
         if chars.codes[i] > 0x20 and chars.rights[i] > chars.lefts[i]),
        None,
    )  # fmt: skip
    if last < 0 or following is None:
        return False
    if chars.turns[last] != UPRIGHT or chars.turns[following] != UPRIGHT:
        return False
    low, high = extent  # the line's, not its last character's (a superscript, then a subscript)
    overlap = min(high, chars.tops[following]) - max(low, chars.bottoms[following])
    height = min(high - low, chars.tops[following] - chars.bottoms[following])
    size = max(chars.font_sizes[last], chars.font_sizes[following], 1.0)
    return (
        height > 0
        and overlap >= ROW_OVERLAP * height
        and chars.lefts[following] >= chars.lefts[last] - 1.0
        and chars.lefts[following] - chars.rights[last] <= SCRIPT_GAP_EMS * size
    )


def new_row(chars: Chars, last: int, index: int) -> bool:
    """A character turned otherwise than the last one (a page's header, then its sideways table's
    title), or a sideways one on another row: its row is across the page."""
    turn = chars.turns[index]
    if chars.codes[index] <= 0x20 or chars.rights[index] <= chars.lefts[index]:
        return False
    if ASLANT in (turn, chars.turns[last]):
        return False  # an aslant glyph in a line (a slanted symbol) stays in it (review of 013)
    if turn != chars.turns[last]:
        return True
    if turn not in (CLOCKWISE, COUNTERCLOCKWISE):
        return False
    height = max(width(chars, index), width(chars, last), 1.0)
    return abs(chars.lefts[index] - chars.lefts[last]) > NEW_ROW_SHARE * height
