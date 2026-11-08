"""Plain text and CSV cut between lines or rows (feature 027, ADR-0047). Text in, parts out.

Text: the parts, put back together, are the file. CSV: a row may span lines inside quotes, so
rows are found by their quotes; every part starts with the header row, and the parts' rows, in
order, are the file's rows.
"""

from clearmd.backend.schemas.split import Cut
from clearmd.backend.services.split.words import count_words


def lines(text: str) -> list[str]:
    return text.splitlines(keepends=True)


def csv_rows(text: str) -> list[str]:
    """The raw rows of a CSV, each with its line break; a quoted field may hold line breaks."""
    rows: list[str] = []
    start = 0
    quoted = False
    for index, char in enumerate(text):
        if char == '"':
            quoted = not quoted  # "" inside a field toggles twice: no change
        elif char == "\n" and not quoted:
            rows.append(text[start : index + 1])
            start = index + 1
    if start < len(text):
        rows.append(text[start:])
    return rows


def balanced_cuts(weights: list[int], count: int) -> list[int]:
    """Where to cut ``weights`` into ``count`` runs as even as possible (never an empty run)."""
    total = sum(weights)
    cuts: list[int] = []
    reached = 0
    for index, weight in enumerate(weights[:-1], start=1):
        reached += weight
        if len(cuts) < count - 1 and reached >= total * (len(cuts) + 1) / count - weight / 2:
            cuts.append(index)
    return cuts


def group(units: list[str], cut: Cut, size: int) -> tuple[list[list[str]], tuple[int, ...]]:
    """Units (lines, rows) grouped whole and in order: into ``size`` parts balanced by words,
    or up to ``size`` words a part (a larger unit alone). Also the parts over the size."""
    weights = [max(1, count_words(unit)) for unit in units]
    groups: list[list[str]] = []
    over: list[int] = []
    if cut is Cut.PARTS:
        bounds = [0, *balanced_cuts(weights, size), len(units)]
        return [units[start:end] for start, end in zip(bounds, bounds[1:], strict=False)], ()
    words = 0
    for unit, weight in zip(units, weights, strict=True):
        if groups and words + weight <= size:
            groups[-1].append(unit)
            words += weight
        else:
            groups.append([unit])
            words = weight
        if words > size and len(groups) not in over:
            over.append(len(groups))
    return groups, tuple(over)


def cut_text(text: str, kind: str, cut: Cut, size: int) -> tuple[tuple[str, ...], tuple[int, ...]]:
    """The parts of a ``kind`` ("txt" or "csv") file, and which are over the size."""
    if kind == "csv":
        rows = csv_rows(text)
        if len(rows) < 2:
            return ((text,) if text else ()), ()
        header, body = rows[0], rows[1:]
        groups, over = group(body, cut, size)
        return tuple(header + "".join(rows_) for rows_ in groups), over
    groups, over = group(lines(text), cut, size)
    return tuple("".join(part) for part in groups), over
