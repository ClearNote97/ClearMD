"""The page's display equations: ranges of line indices (feature 013, ADR-0034)."""

from collections.abc import Sequence

from clearmd.backend.services.conversion.pdf.equations.bars import bar_lines
from clearmd.backend.services.conversion.pdf.equations.joins import joins
from clearmd.backend.services.conversion.pdf.equations.labels import label_lines
from clearmd.backend.services.conversion.pdf.equations.model import Placed
from clearmd.backend.services.conversion.pdf.equations.params import MAX_LINES
from clearmd.backend.services.conversion.pdf.tables import Word


def find_equations(
    lines: list[Placed], words: list[Word], bars: Sequence[tuple[float, float, float]] | None = None
) -> list[range]:
    """The display equations of a page: ranges of its line indices, in reading order. Found by
    their number at the right margin, or (with no number, 015) by a fraction's bar: a short
    line drawn with words right above and below it, on lines that are no prose."""
    if not lines or not words:
        return []
    right_edge = max((line.right for line in lines if not line.other), default=None)
    if right_edge is None:  # a page of tables and pictures only
        return []
    taken: set[int] = set()
    found: list[range] = []
    labels = label_lines(lines, words, right_edge)
    seeds = [(index, index, size, False) for index, size in sorted(labels.items())]
    seeds += [(*seed, True) for seed in bar_lines(lines, words, bars or [], set(labels))]
    for first, last, size, unnumbered in seeds:
        if any(i in taken for i in range(first, last + 1)):
            continue
        stops = set(labels) | taken
        start, end = first, last
        # What is found so far, bottom to top, and the number's size (a subscript's is no measure).
        box = [
            min(line.bottom for line in lines[first : last + 1]),
            max(line.top for line in lines[first : last + 1]),
            size,
        ]
        while (
            start - 1 >= 0
            and first - start < MAX_LINES
            and joins(lines[start - 1], start - 1, box, stops, unnumbered)
        ):
            start -= 1
        while (
            end + 1 < len(lines)
            and end - last < MAX_LINES
            and joins(lines[end + 1], end + 1, box, stops, unnumbered)
        ):
            end += 1
        if end - start + 1 <= MAX_LINES:
            found.append(range(start, end + 1))
            taken.update(range(start, end + 1))
    return sorted(found, key=lambda lines_found: lines_found.start)
