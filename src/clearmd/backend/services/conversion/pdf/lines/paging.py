"""One page's characters split into lines, then tables and equations found (feature 008, 013)."""

import math

from clearmd.backend.services.conversion.pdf.blocks.equation_blocks import place_equations
from clearmd.backend.services.conversion.pdf.blocks.equation_latex import Found
from clearmd.backend.services.conversion.pdf.blocks.tables_on_page import tabled
from clearmd.backend.services.conversion.pdf.decode import LINE_END
from clearmd.backend.services.conversion.pdf.latex import Bar
from clearmd.backend.services.conversion.pdf.lattice import Rule
from clearmd.backend.services.conversion.pdf.lines.assemble import build_line
from clearmd.backend.services.conversion.pdf.lines.breaks import goes_on, new_row
from clearmd.backend.services.conversion.pdf.model import (
    CLOCKWISE,
    COUNTERCLOCKWISE,
    UPRIGHT,
    Boxes,
    Chars,
    Document,
    Page,
)
from clearmd.backend.services.conversion.pdf.tables import Word


def build_page(
    chars: Chars,
    shifts: list[int],
    unmapped: list[bool],
    document: Document,
    rules: list[Rule] | None = None,
    bars: list[Bar] | None = None,
    tight: "Boxes | None" = None,
) -> Page:
    page = Page()
    words: dict[int, list[Word]] = {UPRIGHT: [], CLOCKWISE: [], COUNTERCLOCKWISE: []}
    start = 0
    last = -1  # the last character drawn (with a width): where a sideways row goes on from
    extent = [math.inf, -math.inf]  # the line's bottom and top so far
    for index in range(len(chars.codes) + 1):
        ended = index == len(chars.codes) or (
            chars.codes[index] == LINE_END and not goes_on(chars, last, index, extent)
        )
        if not ended and last >= start and new_row(chars, last, index):
            ended = True  # PDFium runs a sideways table's rows into one line: one per row
            next_start = index
        else:
            next_start = index + 1
        if ended:
            if index > start:
                line = build_line(chars, range(start, index), shifts, unmapped, document, words)
                if line.text.strip():
                    page.lines.append(line)
            start = next_start
            extent[:] = [math.inf, -math.inf]
        if (
            index < len(chars.codes)
            and chars.codes[index] > 0x20  # a space PDFium adds is drawn nowhere in particular
            and chars.rights[index] > chars.lefts[index]
        ):
            last = index
            extent[0] = min(extent[0], chars.bottoms[index])
            extent[1] = max(extent[1], chars.tops[index])
    lines = tabled(page.lines, words, rules or [])
    found = Found(chars, shifts, unmapped, bars or [], tight)
    page.lines = place_equations(lines, words[UPRIGHT], found)
    return page
