"""An equation's characters and bars as LaTeX, and what it is rebuilt from (feature 015).

``to_latex`` is read here, at call time: a test that replaces it patches this module.
"""

from dataclasses import dataclass

from clearmd.backend.services.conversion.pdf.decode import LINE_END, SKIPPED, SOFT_HYPHENS, decoded
from clearmd.backend.services.conversion.pdf.latex import Bar, Glyph, to_latex
from clearmd.backend.services.conversion.pdf.model import UPRIGHT, Boxes, Chars, Line


@dataclass(frozen=True)
class Found:
    """What an equation is rebuilt from: the page's characters, its bars, and PDFium's tight box
    of a character (its loose one reaches past the letter: too coarse to place a script)."""

    chars: Chars
    shifts: list[int]
    unmapped: list[bool]
    bars: list[Bar]
    tight: Boxes | None = None


def latex_of(group: list[Line], found: Found, box: tuple[float, float, float, float]) -> str:
    """The equation's characters and the bars within its box, as LaTeX ("" when unsure)."""
    chars = found.chars
    glyphs: list[Glyph] = []
    for line in group:
        start, stop = line.span
        high = 0  # a character past U+FFFF comes as two halves (as ``build_line`` reads them)
        for index in range(start, min(stop, len(chars.codes))):
            raw_code = chars.codes[index]
            if raw_code in SKIPPED or raw_code == LINE_END:
                continue
            font = chars.fonts[index]
            if found.unmapped[font] and not found.shifts[font]:
                return ""  # a font without a map: its letters are wrong (review of 015)
            code = decoded(raw_code, found.shifts[font])
            if high and not 0xDC00 <= code < 0xE000:
                return ""  # a first half with no second: unreadable
            if 0xD800 <= code < 0xDC00:
                high = code
                continue
            if 0xDC00 <= code < 0xE000:
                if not high:
                    return ""
                code, high = 0x10000 + ((high - 0xD800) << 10) + (code - 0xDC00), 0
            if code in (0x09, 0x20):
                continue
            if code < 0x20 or code == 0x7F or code > 0x10FFFF or code == 0xFFFD:
                return ""  # unreadable, or a soft hyphen: never dropped unseen
            if code in SOFT_HYPHENS:
                return ""
            if chars.rights[index] <= chars.lefts[index] or chars.turns[index] != UPRIGHT:
                return ""  # a character drawn nowhere, or turned: no place to read it from
            tight = found.tight(index) if found.tight is not None else None
            left, right, bottom, top = tight or (
                chars.lefts[index],
                chars.rights[index],
                chars.bottoms[index],
                chars.tops[index],
            )
            glyphs.append(
                Glyph(chr(code), left, right, bottom, top,
                      chars.font_sizes[index], chars.baselines[index])
            )  # fmt: skip
        if high:
            return ""  # a line that ends on a first half
    low, high_edge, left_edge, right_edge = box
    bars = [
        bar for bar in found.bars
        if low - 1 <= bar.at <= high_edge + 1
        and left_edge <= (bar.left + bar.right) / 2 <= right_edge
    ]  # fmt: skip
    return to_latex(glyphs, bars) or ""
