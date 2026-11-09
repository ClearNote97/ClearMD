"""Where a PDF's parts start and end (features 023, 024): by count, by pages, by words."""

from clearmd.backend.schemas.split import Cut


def page_ranges(pages: int, cut: Cut, size: int) -> tuple[tuple[int, int], ...]:
    """The parts' first and last pages (1-based, inclusive). Into N parts: as even as possible,
    the first ones a page longer; never more parts than pages, never an empty one."""
    if pages <= 0:
        return ()
    if cut is Cut.PAGES:
        return tuple((first, min(first + size - 1, pages)) for first in range(1, pages + 1, size))
    count = min(size, pages)
    base, extra = divmod(pages, count)
    ranges = []
    first = 1
    for index in range(count):
        length = base + (1 if index < extra else 0)
        ranges.append((first, first + length - 1))
        first += length
    return tuple(ranges)


def word_ranges(
    words: tuple[int, ...], size: int
) -> tuple[tuple[tuple[int, int], ...], tuple[int, ...]]:
    """Whole pages, in order, up to ``size`` words a part (feature 024); a page larger than
    ``size`` is a part alone. The ranges, and which parts are over the size."""
    ranges: list[tuple[int, int]] = []
    over: list[int] = []
    total = 0
    for page, count in enumerate(words, start=1):
        if ranges and total + count <= size:
            ranges[-1] = (ranges[-1][0], page)
            total += count
        else:
            ranges.append((page, page))
            total = count
        if total > size and len(ranges) not in over:
            over.append(len(ranges))
    return tuple(ranges), tuple(over)
