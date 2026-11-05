"""Emphasis Markdown can hold: styles that would show as literal ``*`` or ``~`` are dropped."""

from clearmd.backend.services.conversion.inline.commonmark import flanking
from clearmd.backend.services.conversion.inline.delimiters import (
    EMPHASIS,
    active,
    closer,
    opener,
    without,
)
from clearmd.backend.services.conversion.inline.pieces import Text, split_space
from clearmd.backend.services.conversion.markdown_out import escape_text, inline_code


def _runs(
    tokens: list[tuple[str, str, bool]], before: str, after: str
) -> tuple[set[str], set[str]]:
    """The keys whose delimiters at one boundary would show literally: (closing, opening). The
    boundary's text is ``before``, the closers and openers ``tokens``, then ``after``; each
    maximal run of the same delimiter character is judged by its real neighbours."""
    chars = [before, *(text for text, _, _ in tokens), after]
    closing: set[str] = set()
    opening: set[str] = set()
    position = 0
    while position < len(tokens):
        text, key, _ = tokens[position]
        end = position
        if key in EMPHASIS:
            while (
                end + 1 < len(tokens)
                and tokens[end + 1][1] in EMPHASIS
                and tokens[end + 1][0][0] == text[0]
            ):
                end += 1
            run = tokens[position : end + 1]
            left, right = chars[position][-1], chars[end + 2][0]
            if any(not opens for *_, opens in run) and not flanking(left, right, left=False):
                closing.update(key for _, key, opens in run if not opens)
            if any(opens for *_, opens in run) and not flanking(left, right, left=True):
                opening.update(key for _, key, opens in run if opens)
        position = end + 1
    return closing, opening


MAX_EMPHASIS_PASSES = 8


def safe_emphasis(group: list[Text]) -> tuple[list[Text], int]:
    """The group with the emphasis Markdown would show as literal ``*`` or ``~`` left out, and
    how many runs lost a style. Each pass replays ``styled`` (the same stack of open styles) and
    judges every delimiter run between two touching runs of text by the characters actually
    written around it: the text, ClearMD's own ``<u>`` or ``<sup>`` tags, other delimiters
    (``word**"quoted"**s`` and ``**<u>a</u>**b`` show their asterisks). A failing style is
    dropped from the run next to it, and the pass is repeated; after a few passes the group
    loses its emphasis (plain text is always safe). Each pass is linear."""
    split = [split_space(piece.text) for piece in group]
    cores = [index for index, (_, core, _) in enumerate(split) if core]
    if len(cores) < 2:
        return group, 0
    written = [
        inline_code(split[i][1]) if group[i].props.mono else escape_text(split[i][1]) for i in cores
    ]
    touching = [False] + [
        not (split[cores[k - 1]][2] or split[cores[k]][0])
        and all(not group[i].text for i in range(cores[k - 1] + 1, cores[k]))
        for k in range(1, len(cores))
    ]
    props = [group[i].props for i in cores]
    dropped = 0
    for _ in range(MAX_EMPHASIS_PASSES):
        failing: dict[int, set[str]] = {}
        opened: list[str] = []
        for k in range(len(cores)):
            wanted = active(props[k])
            keep = 0
            while keep < len(opened) and opened[keep] in wanted:
                keep += 1
            tokens = [(closer(key), key, False) for key in reversed(opened[keep:])]
            opened = opened[:keep]
            for key in wanted:
                if key not in opened:
                    tokens.append((opener(key), key, True))
                    opened.append(key)
            if k and touching[k] and tokens:
                closing, opening = _runs(tokens, written[k - 1][-1], written[k][0])
                if closing:
                    failing.setdefault(k - 1, set()).update(closing)
                if opening:
                    failing.setdefault(k, set()).update(opening)
        if not failing:
            break
        for k, keys in failing.items():
            props[k] = without(props[k], keys)
            dropped += 1
    else:  # still failing: no emphasis at all in this group
        for k, value in enumerate(props):
            if any(getattr(value, key) for key in EMPHASIS):
                props[k] = without(value, set(EMPHASIS))
                dropped += 1
    if not dropped:
        return group, 0
    safe = list(group)
    for k, index in enumerate(cores):
        piece = group[index]
        safe[index] = Text(piece.text, props[k], piece.link, piece.literal)
    return safe, dropped
