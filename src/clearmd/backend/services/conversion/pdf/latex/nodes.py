"""The pieces an equation is made of: glyphs, bars and the nodes built from them (015)."""

import math
import unicodedata
from dataclasses import dataclass, field

from clearmd.backend.services.conversion.pdf.latex.symbols import (
    ACCENTS,
    BIG_OPERATORS,
    CLOSERS,
    OPENERS,
    char_latex,
)

AXIS_EMS = 0.25  # the math axis (where a fraction's bar stands) above the baseline


@dataclass(frozen=True)
class Glyph:
    """A character as drawn: its tight box, the size it is set in, and its baseline."""

    text: str
    left: float
    right: float
    bottom: float
    top: float
    size: float
    baseline: float


@dataclass(frozen=True)
class Bar:
    """A thin horizontal line drawn among the characters: a fraction's bar, an overline."""

    left: float
    right: float
    at: float


@dataclass
class Node:
    latex: str
    left: float
    right: float
    bottom: float
    top: float
    size: float
    axis: float  # the height its row's axis passes at
    char: str = ""  # a single character's text ("" for a built piece)
    tall: bool = False  # a bracket spanning more than a line, or a sum
    scripts: dict[str, str] = field(default_factory=dict)  # "^", "_" (or limits: "over", "under")
    reach: float = -math.inf  # how far right its scripts go

    @property
    def middle(self) -> float:
        return (self.bottom + self.top) / 2

    @property
    def middle_x(self) -> float:
        return (self.left + self.right) / 2


def node_of(glyph: Glyph) -> Node:
    if glyph.text in ACCENTS:  # before NFKC, which turns "¯" into a space and a mark
        axis = glyph.baseline + AXIS_EMS * glyph.size
        box = (glyph.left, glyph.right, glyph.bottom, glyph.top)
        return Node(ACCENTS[glyph.text], *box, glyph.size, axis, char=glyph.text)
    char = unicodedata.normalize("NFKC", glyph.text) if len(glyph.text) == 1 else glyph.text
    if char in BIG_OPERATORS or char in OPENERS or char in CLOSERS:
        axis = (glyph.bottom + glyph.top) / 2  # drawn around the axis, whatever its baseline
    else:
        axis = glyph.baseline + AXIS_EMS * glyph.size
    return Node(
        char_latex(char),
        glyph.left,
        glyph.right,
        glyph.bottom,
        glyph.top,
        glyph.size,
        axis,
        char=char,
    )
