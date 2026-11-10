"""Plain text and CSV cut between lines or rows (feature 027, ADR-0047). Text in, parts out.

Text: the parts, put back together, are the file. CSV: a row may span lines inside quotes, so
rows are found by their quotes; every part starts with the header row, and the parts' rows, in
order, are the file's rows.
"""

from clearmd.backend.schemas.split import Cut
from clearmd.backend.services.split.words import count_words


def lines(text: str) -> list[str]:
    return text.splitlines(keepends=True)


DELIMITERS = ",;\t|"


def csv_rows(text: str) -> list[str]:
    """The raw rows of a CSV, each with its line break; a quoted field may hold line breaks.
    A quote opens a field only at its start (RFC 4180): an inch mark in the middle of a field
    ("24\" monitor") is text, never the start of a quoted field (audit v4, B1-05)."""
    rows: list[str] = []
    start = 0
    quoted = False
    field_start = True
    index = 0
    while index < len(text):
        char = text[index]
        if quoted:
            if char == '"':
                if text[index + 1 : index + 2] == '"':
                    index += 1  # an escaped quote inside the field
                else:
                    quoted = False
        elif char == '"' and field_start:
            quoted = True
        elif char == "\n":
            rows.append(text[start : index + 1])
            start = index + 1
            field_start = True
            index += 1
            continue
        field_start = (not quoted) and char in DELIMITERS
        index += 1
    if start < len(text):
        rows.append(text[start:])
    return rows


def balanced_cuts(weights: list[int], count: int) -> list[int]:
    """Where to cut ``weights`` into ``count`` runs as even as possible (never an empty run).
    With at least ``count`` units there are always ``count`` runs: when the weight is at the end,
    the remaining boundaries are cut (audit 2026-11-09, B1-02)."""
    total = sum(weights)
    cuts: list[int] = []
    reached = 0
    units = len(weights)
    for index, weight in enumerate(weights[:-1], start=1):
        reached += weight
        wanted = count - 1 - len(cuts)
        if wanted <= 0:
            break
        even = reached >= total * (len(cuts) + 1) / count - weight / 2
        if even or units - index <= wanted:  # no boundary left to spare
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
