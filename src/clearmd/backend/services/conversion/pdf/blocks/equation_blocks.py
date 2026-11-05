"""Each display equation's scattered lines, one block that keeps their layout (feature 013, 015)."""

from clearmd.backend.services.conversion.pdf.blocks.equation_latex import Found, latex_of
from clearmd.backend.services.conversion.pdf.blocks.laid_out import laid_out
from clearmd.backend.services.conversion.pdf.equations import Placed, find_equations
from clearmd.backend.services.conversion.pdf.model import UPRIGHT, Line
from clearmd.backend.services.conversion.pdf.tables import Word


def place_equations(
    lines: list[Line], words: list[Word], found_on: Found | None = None
) -> list[Line]:
    """Each display equation's scattered lines, one block that keeps their layout, rebuilt as
    LaTeX when every piece of it is understood (015)."""
    placed = [
        Placed(line.text, line.top, line.bottom, line.size, line.right,
               bool(line.table or line.image or line.turn != UPRIGHT), line.left)
        for line in lines
    ]  # fmt: skip
    bars = [(bar.left, bar.right, bar.at) for bar in found_on.bars] if found_on else []
    for found in reversed(find_equations(placed, words, bars)):
        group = lines[found.start : found.stop]
        top, bottom = max(line.top for line in group), min(line.bottom for line in group)
        left, right = min(line.left for line in group), max(line.right for line in group)
        highest = max(group, key=lambda line: line.top)
        lowest = min(group, key=lambda line: line.bottom)
        # A font's boxes reach past its letters: never into the lines just above and below it
        # (across the equation, not a note beside it), never into its own first or last row.
        if found.start > 0:
            above = lines[found.start - 1]
            if above.left < right and above.right > left and bottom < above.bottom < top:
                top = max(above.bottom, highest.bottom)
        if found.stop < len(lines):
            below = lines[found.stop]
            if below.left < right and below.right > left and bottom < below.top < top:
                bottom = min(below.top, lowest.top)
        block = Line(
            "",
            0.0,  # a block, not text: never a footnote, a heading, a running line (review of 013)
            False,
            top,
            bottom,
            left=min(line.left for line in group),
            right=max(line.right for line in group),
            equation=laid_out(group),
            latex=latex_of(group, found_on, (bottom, top, left, right)) if found_on else "",
        )
        lines = [*lines[: found.start], block, *lines[found.stop :]]
    return lines
