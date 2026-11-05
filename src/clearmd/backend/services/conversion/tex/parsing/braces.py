"""Where a brace closes: a scan for small texts, the pairs of a large one computed once."""

import bisect
from array import array
from functools import lru_cache

_SMALL_TEXT = 4096  # scanned directly; larger texts get their pairs computed once


def _scan_end(text: str, start: int, comments: bool) -> int:
    depth = 0
    index = start
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "%" and comments:
            line_end = text.find("\n", index)
            if line_end == -1:
                return -1
            index = line_end + 1
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return -1


@lru_cache(maxsize=4)
def _brace_pairs(text: str, comments: bool) -> tuple[array[int], array[int]]:
    """Every matched ``{`` of a large text and its ``}``, in one pass: two compact arrays
    (opening positions, sorted, and their closings), about 16 bytes per pair."""
    pairs: list[tuple[int, int]] = []
    open_at: list[int] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "%" and comments:
            line_end = text.find("\n", index)
            index = len(text) if line_end == -1 else line_end + 1
            continue
        if char == "{":
            open_at.append(index)
        elif char == "}" and open_at:
            pairs.append((open_at.pop(), index))
        index += 1
    pairs.sort()
    return array("q", (o for o, _ in pairs)), array("q", (c for _, c in pairs))


def forget_brace_pairs() -> None:
    """Free the pairs kept for the large texts of the document just converted."""
    _brace_pairs.cache_clear()


def balanced_end(text: str, start: int, *, comments: bool = True) -> int:
    """The index of the ``}`` closing the ``{`` at ``start``, or -1. Linear over a document:
    a large text's pairs are found once, not once per unclosed brace."""
    if len(text) < _SMALL_TEXT:
        return _scan_end(text, start, comments)
    openings, closings = _brace_pairs(text, comments)
    index = bisect.bisect_left(openings, start)
    return closings[index] if index < len(openings) and openings[index] == start else -1
