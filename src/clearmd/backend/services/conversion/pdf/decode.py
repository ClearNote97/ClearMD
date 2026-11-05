"""Reading back the codes of a font PDFium has no map for (feature 008, ADR-0030).

A font whose codes are letters moved by one distance is read back with ``shift`` and
``decoded``; both the lines and the equations use them.
"""

from collections import Counter

LINE_END = 0x0A
SKIPPED = {0x0D, 0xFEFF}
SOFT_HYPHENS = {0x02, 0xAD, 0xFFFE}  # what PDFium gives for a hyphen that breaks a word
MIN_SHIFT_SHARE = 0.03  # a font whose text holds this share of control characters is suspect
MIN_LETTER_SHARE = 0.75  # and is read back only if its moved codes are then mostly letters
VOWELS = frozenset("aeiouáéíóúAEIOUÁÉÍÓÚ")
# A TrueType font embedded without a character map often numbers its glyphs in the Macintosh
# standard order (Apple's "post" table): glyph 3 is the space, 36 is "A", so code + 29 is the
# letter, and glyphs 98-198 are these. Past 198 a font's own order differs: unreadable.
MAC_ORDER_SHIFT = 29
_MAC_ORDER = (
    "ÄÅÇÉÑÖÜáàâäãåçéèêëíìîïñóòôöõúùûü†°¢£§•¶ß®©™´¨≠ÆØ∞±≤≥¥µ∂∑∏π∫ªºΩæø¿¡¬√ƒ≈∆«»… "
    "ÀÃÕŒœ–—“”‘’÷◊ÿŸ⁄¤‹›ﬁﬂ‡·‚„‰"
)
_MAC_FIRST = 98


def shift(codes: Counter[int]) -> int:
    """How far one font's codes are moved from the letters they draw (0: not moved). The space is
    the commonest character of any text: moved to a control character, it gives the distance;
    the rest must then be mostly letters, with vowels among them, as words are."""
    total = sum(codes.values())
    controls = {code: n for code, n in codes.items() if code < 0x20 and code not in (9, 10, 13)}
    if not controls or sum(controls.values()) < MIN_SHIFT_SHARE * total:
        return 0
    space = max(controls, key=controls.__getitem__)
    distance = 0x20 - space
    rest = {code: n for code, n in codes.items() if code != space and code not in SKIPPED}
    moved = {chr(decoded(code, distance)): n for code, n in rest.items() if code < 0x110000}
    letters = sum(n for char, n in moved.items() if char.isalpha())
    vowels = sum(n for char, n in moved.items() if char in VOWELS)
    others = sum(rest.values()) or 1
    return distance if letters >= MIN_LETTER_SHARE * others and vowels >= 0.2 * letters else 0


def decoded(code: int, distance: int) -> int:
    if not distance:
        return code
    if distance == MAC_ORDER_SHIFT and code >= _MAC_FIRST:
        index = code - _MAC_FIRST
        return ord(_MAC_ORDER[index]) if index < len(_MAC_ORDER) else 0xFFFD
    moved = code + distance
    return moved if moved < 0x80 else 0xFFFD
