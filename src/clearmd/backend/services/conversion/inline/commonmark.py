"""CommonMark's emphasis algorithm, exact: flanking runs, the rule of three, GFM strike-through."""

import unicodedata
from typing import Any


def _kind(char: str) -> str:
    """CommonMark's classes for the characters around a delimiter run."""
    if char.isspace():
        return "space"
    return "punctuation" if unicodedata.category(char)[0] in "PS" else "word"


def flanking(before: str, after: str, *, left: bool) -> bool:
    """CommonMark's left- (``left``) or right-flanking delimiter run."""
    near, far = (_kind(after), _kind(before)) if left else (_kind(before), _kind(after))
    return near != "space" and (near != "punctuation" or far != "word")


_ASCII_PUNCTUATION = frozenset("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")


def _code_span_end(text: str, start: int, end: int) -> int:
    """Where the code span opened by the backtick run ``text[start:end]`` ends: after the next run
    of the same length, or at ``end`` when there is none (the backticks are then text)."""
    length = end - start
    position = end
    while position < len(text):
        if text[position] != "`":
            position += 1
            continue
        run_end = position
        while run_end < len(text) and text[run_end] == "`":
            run_end += 1
        if run_end - position == length:
            return run_end
        position = run_end
    return end


def unpaired_delimiters(text: str) -> bool:
    """Whether a viewer would show one of ClearMD's own ``*`` or ``~`` literally in ``text`` (a
    run of inline text as ``styled`` writes it: the document's own ``*`` and ``~`` are escaped).

    CommonMark's emphasis algorithm (spec 0.31, "process emphasis"), in the standard library:
    delimiter runs with their flanking, the rule of three, openers bottom per kind; GFM's
    strike-through pairs runs of exactly two tildes. Code spans and escapes are skipped."""
    runs: list[list[Any]] = []  # [character, count, can_open, can_close, original count]
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text) and text[index + 1] in _ASCII_PUNCTUATION:
            index += 2
            continue
        if char == "`":
            end = index
            while end < len(text) and text[end] == "`":
                end += 1
            index = _code_span_end(text, index, end)
            continue
        if char in "*~":
            end = index
            while end < len(text) and text[end] == char:
                end += 1
            before = text[index - 1] if index else " "
            after = text[end] if end < len(text) else " "
            opens = flanking(before, after, left=True)
            closes = flanking(before, after, left=False)
            if char == "~" and end - index != 2:
                return True  # GFM: one tilde is text, three or more are not strike-through
            runs.append([char, end - index, opens, closes, end - index])
            index = end
            continue
        index += 1
    # The openers still unpaired, in order, with a sequence number; a closer pairs with the
    # nearest compatible one. One further down would leave the ones above it unpaired (shown as
    # written): the answer is already known. ``bottom`` keeps failed searches from rescanning.
    stack: list[tuple[int, list[Any]]] = []
    bottom: dict[tuple[str, bool, int], int] = {}
    for sequence, run in enumerate(runs):
        char, _, opens, closes, original = run
        key = (char, opens, original % 3)
        while closes and run[1]:
            found = -1
            position = len(stack) - 1
            while position >= 0 and stack[position][0] >= bottom.get(key, 0):
                candidate = stack[position][1]
                if candidate[0] == char and _pairs(candidate, run):
                    found = position
                    break
                position -= 1
            if found == -1:
                bottom[key] = sequence
                break
            if found != len(stack) - 1:
                return True
            opener = stack[-1][1]
            use = 2 if run[1] >= 2 and opener[1] >= 2 else 1
            opener[1] -= use
            run[1] -= use
            if not opener[1]:
                stack.pop()
        if run[1]:
            if not opens:
                return True  # a closer left over that cannot open
            stack.append((sequence, run))
    return bool(stack)


def _pairs(opener: list[Any], closer: list[Any]) -> bool:
    """CommonMark's rule of three for ``*``; GFM strike-through pairs equal runs of ``~``."""
    if opener[0] == "~":
        return bool(opener[1] == closer[1])
    both = opener[3] or closer[2]
    total = opener[4] + closer[4]
    return not (both and total % 3 == 0 and not (opener[4] % 3 == 0 and closer[4] % 3 == 0))
