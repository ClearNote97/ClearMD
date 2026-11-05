"""An equation's number as a tag, and the balance check of the result (feature 015)."""

import re

from clearmd.backend.services.conversion.pdf.latex.nodes import Glyph

LABEL_GAP = 1.5  # of the text's size: an equation's number stands this far from the rest
_LABEL = re.compile(r"\((\d{1,3}[a-z]?)\)")


def without_label(glyphs: list[Glyph]) -> tuple[list[Glyph], str]:
    """The equation's number, "(7)" at its right, set apart: written as ``\\tag{7}``."""
    ordered = sorted(glyphs, key=lambda glyph: glyph.left)
    for count in range(3, 6):
        if count > len(ordered):
            break
        tail = ordered[-count:]
        found = _LABEL.fullmatch("".join(glyph.text for glyph in tail))
        if found is None:
            continue
        rest = ordered[:-count]
        size = max(glyph.size for glyph in tail)
        start = tail[0].left
        if not rest or max(glyph.right for glyph in rest) <= start - LABEL_GAP * size:
            return rest, found.group(1)
    return glyphs, ""


def balanced(latex: str) -> bool:
    """Braces, ``\\left``/``\\right`` and ``\\begin``/``\\end`` in pairs (a check of the
    writer: never a formula a viewer would refuse)."""
    depth = 0
    escaped = False
    for char in latex:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                return False
    if depth:
        return False
    lefts = len(re.findall(r"\\left(?![a-z])", latex))
    rights = len(re.findall(r"\\right(?![a-z])", latex))
    return lefts == rights and latex.count(r"\begin{") == latex.count(r"\end{")
