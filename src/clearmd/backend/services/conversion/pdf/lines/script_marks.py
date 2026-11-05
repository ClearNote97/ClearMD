"""Which characters of a line are scripts, raised or lowered from the text (feature 014)."""

from collections import Counter

from clearmd.backend.services.conversion.pdf.model import UPRIGHT, Chars

SCRIPT_SIZE = 0.85  # a character this much smaller than its line's text may be a script
RAISED_EMS = 0.12  # its baseline this far above the line's (in its size) is a superscript
LOWERED_EMS = 0.08  # this far below, a subscript
BASE_SHARE = 0.15  # a character within this share of the text's size is text
TEXT_SHARE = 0.2  # of a line's characters: a size this many share may be the text's
DELIMITER_RATIO = 1.6  # larger than the commonest size: a tall brace or bracket


def script_marks(chars: Chars, visible: list[int]) -> dict[int, str]:
    """Each script's character and its kind: "^" raised, "_" lowered."""
    upright = [i for i in visible if chars.turns[i] == UPRIGHT and chars.font_sizes[i] > 0]
    if len(upright) < 2:
        return {}
    counts = Counter(round(chars.font_sizes[i], 1) for i in upright)
    commonest = counts.most_common(1)[0][0]
    # The text's size: the largest one many characters share ("((xᵗ⁺¹" has more script than
    # text), never a tall delimiter's.
    shared = [
        size for size, count in counts.items()
        if count >= max(2, TEXT_SHARE * len(upright)) and size <= DELIMITER_RATIO * commonest
    ]  # fmt: skip
    text_size = max(shared, default=commonest)
    # The text a script is set on: letters and digits of the text's size (never a "∑" or "=",
    # whose baseline is the symbol's own).
    level = {
        i for i in upright
        if abs(chars.font_sizes[i] - text_size) <= BASE_SHARE * text_size
        and (chr(chars.codes[i]).isalnum() or chr(chars.codes[i]) == ")")
    }  # fmt: skip
    normal = [i for i in upright if i in level]
    if not normal:
        return {}
    # Raised or lowered from the text it is set on, the character before it (or after): a PDFium
    # "line" may hold two rows of a paragraph, never one baseline. Found in one pass each way.
    previous: list[int | None] = []
    seen: int | None = None
    for i in upright:
        previous.append(seen)
        if i in level:
            seen = i
    following: list[int | None] = [None] * len(upright)
    seen = None
    for position in range(len(upright) - 1, -1, -1):
        following[position] = seen
        if upright[position] in level:
            seen = upright[position]
    small = [chars.font_sizes[i] < SCRIPT_SIZE * text_size for i in upright]
    marks: dict[int, str] = {}
    for position, i in enumerate(upright):
        if not small[position]:
            continue
        lone = (
            0 < position < len(upright) - 1 and not small[position - 1] and not small[position + 1]
        )
        if lone and not chr(chars.codes[i]).isalnum():
            continue  # an operator set smaller between two terms ("1 ∗ 0.169"), no script
        base = previous[position]
        if base is None:
            base = following[position]
        if base is None:
            base = normal[0]
        shift = chars.baselines[i] - chars.baselines[base]
        if shift > RAISED_EMS * text_size:
            marks[i] = "^"
        elif shift < -LOWERED_EMS * text_size:
            marks[i] = "_"
    return marks
