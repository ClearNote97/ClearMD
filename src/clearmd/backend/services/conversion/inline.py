"""Inline text as ClearMD writes it, shared by its own converters (``.odt``, the HTML article
mode): runs of text with their properties, joined and escaped through ``markdown_out``, with
emphasis Markdown can hold only (an exact check of CommonMark's emphasis algorithm), links by the
rules of ADR-0023, and a growth budget for what a link repeats. Standard library only."""

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Any

from clearmd.backend.services.conversion.markdown_out import (
    ENTITY,
    SAFE_LINK,
    escape_text,
    inline_code,
    join_pieces,
    link_target,
)

LINE_BREAK = "  \n"
# The image placeholder's word in the document's language (English otherwise).
IMAGE_WORD = {"es": "Imagen", "pt": "Imagem", "fr": "Image", "it": "Immagine", "de": "Bild"}
_WHITESPACE = re.compile(r"[ \t\r\n]+")


@dataclass(frozen=True)
class TextProps:
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    position: str = ""  # "super", "sub" or ""
    mono: bool = False
    hidden: bool = False


@dataclass(frozen=True)
class Text:
    text: str
    props: TextProps
    link: str | None
    literal: bool = False  # spaces and tabs written as such (text:s, text:tab): never collapsed


@dataclass(frozen=True)
class Raw:
    markdown: str  # written by ClearMD itself: a footnote reference, a line break, a placeholder


Piece = Text | Raw
_ORDER = ("bold", "italic", "strike", "underline", "position")
_OPEN = {"bold": "**", "italic": "*", "strike": "~~", "underline": "<u>"}
_CLOSE = {"bold": "**", "italic": "*", "strike": "~~", "underline": "</u>"}


def _active(props: TextProps) -> list[str]:
    found = []
    for key in _ORDER:
        value = getattr(props, key)
        if value:
            found.append(f"position:{value}" if key == "position" else key)
    return found


_POSITION_TAG = {"super": "sup", "sub": "sub"}


def _opener(key: str) -> str:
    if key.startswith("position:"):
        return f"<{_POSITION_TAG[key.split(':')[1]]}>"
    return _OPEN[key]


def _closer(key: str) -> str:
    if key.startswith("position:"):
        return f"</{_POSITION_TAG[key.split(':')[1]]}>"
    return _CLOSE[key]


class InlineWriter:
    """Pieces → Markdown. ``spend`` charges what a link's address repeats to the document's growth
    budget; ``dropped`` counts the runs whose emphasis Markdown could not hold (for a note)."""

    def __init__(self, spend: Callable[[int], bool]) -> None:
        self._spend = spend
        self.dropped = 0

    def normalize(self, pieces: list[Piece]) -> list[Piece]:
        """Whitespace as HTML and ODF read it: runs collapse to one space, none at the start or
        the end; equal neighbours are merged (their texts joined once: linear)."""
        cleaned: list[Piece] = []
        for piece in pieces:
            if isinstance(piece, Text) and not piece.literal:
                text = _WHITESPACE.sub(" ", piece.text)
                previous = cleaned[-1] if cleaned else None
                ends_in_space = (
                    previous is None
                    or (isinstance(previous, Raw) and previous.markdown == LINE_BREAK)
                    or (isinstance(previous, Text) and previous.text.endswith(" "))
                )
                if ends_in_space:
                    text = text.lstrip(" ")
                if not text:
                    continue
                piece = Text(text, piece.props, piece.link)
            cleaned.append(piece)
        out: list[Piece] = []
        merged: list[str] = []  # the texts that make out[-1], joined when the run ends

        def close() -> None:
            last = out[-1] if out else None
            if merged and isinstance(last, Text):
                out[-1] = Text("".join(merged), last.props, last.link, literal=True)
            merged.clear()

        for piece in cleaned:
            last = out[-1] if out else None
            if (
                isinstance(piece, Text)
                and isinstance(last, Text)
                and (last.props, last.link) == (piece.props, piece.link)
            ):
                if not merged:
                    merged.append(last.text)
                merged.append(piece.text)
                continue
            close()
            out.append(piece)
        close()
        while out and isinstance(out[-1], Text) and not out[-1].text.strip():
            out.pop()
        if out and isinstance(out[-1], Text):
            out[-1] = Text(out[-1].text.rstrip(" "), out[-1].props, out[-1].link, literal=True)
        return out

    def write(self, pieces: list[Piece]) -> str:
        parts: list[str] = []
        index = 0
        while index < len(pieces):
            piece = pieces[index]
            if isinstance(piece, Text) and piece.link is not None:
                group = [piece]
                while (
                    index + 1 < len(pieces)
                    and isinstance(pieces[index + 1], Text)
                    and pieces[index + 1].link == piece.link  # type: ignore[union-attr]
                ):
                    index += 1
                    group.append(pieces[index])  # type: ignore[arg-type]
                parts.append(self._link(piece.link, group))
            elif isinstance(piece, Text):
                group = [piece]
                while (
                    index + 1 < len(pieces)
                    and isinstance(pieces[index + 1], Text)
                    and pieces[index + 1].link is None  # type: ignore[union-attr]
                ):
                    index += 1
                    group.append(pieces[index])  # type: ignore[arg-type]
                parts.append(self.style(group))
            else:
                parts.append(piece.markdown)
            index += 1
        return join_pieces(parts)

    def style(self, group: list[Text]) -> str:
        safe, dropped = safe_emphasis(group)
        written = styled(safe)
        if unpaired_delimiters(written):  # the pairing itself fails (CommonMark's rule of 3…)
            plain = [Text(p.text, without(p.props, set(EMPHASIS)), p.link, p.literal) for p in safe]
            dropped += sum(
                1 for old, new in zip(safe, plain, strict=True) if old.props != new.props
            )
            written = styled(plain)
        self.dropped += dropped
        return written

    def _link(self, url: str, group: list[Text]) -> str:
        written = self.style([Text(g.text, g.props, None, g.literal) for g in group])
        lead, text, trail = split_space(written)  # the spaces around the text stay outside the link
        url = url.strip()
        # Each piece of a link repeats its address: charged, and past the budget only the text.
        if not url or not self._spend(len(url)):
            return written
        if not SAFE_LINK.match(url) or ENTITY.search(url):  # javascript: never becomes a link
            shown = f"{text} ({inline_code(url)})" if text else inline_code(url)
        else:
            shown = f"[{text or escape_text(url)}]({link_target(url)})"
        return lead + shown + trail


def split_space(text: str) -> tuple[str, str, str]:
    core = text.strip(" \t")
    if not core:
        return text, "", ""
    start = text.index(core)
    return text[:start], core, text[start + len(core) :]


def styled(group: list[Text]) -> str:
    """Runs of text with their delimiters opened and closed as the properties change."""
    out: list[str] = []
    opened: list[str] = []
    pending: list[str] = []  # spaces between two runs, joined once
    for piece in group:
        lead, core, trail = split_space(piece.text)
        if not core:
            pending.append(piece.text)
            continue
        wanted = _active(piece.props)
        keep = 0
        while keep < len(opened) and opened[keep] in wanted:
            keep += 1
        out.extend(_closer(key) for key in reversed(opened[keep:]))
        opened = opened[:keep]
        out.append("".join(pending) + lead)
        pending.clear()
        for key in wanted:
            if key not in opened:
                out.append(_opener(key))
                opened.append(key)
        out.append(inline_code(core) if piece.props.mono else escape_text(core))
        pending.append(trail)
    out.extend(_closer(key) for key in reversed(opened))
    out.append("".join(pending))
    # The same joining rules as between pieces: a backtick of the text never glues to a code span.
    return join_pieces(out)


# --- Emphasis Markdown can hold -------------------------------------------------------------

EMPHASIS = ("bold", "italic", "strike")


def _kind(char: str) -> str:
    """CommonMark's classes for the characters around a delimiter run."""
    if char.isspace():
        return "space"
    return "punctuation" if unicodedata.category(char)[0] in "PS" else "word"


def without(props: TextProps, keys: set[str]) -> TextProps:
    return replace(
        props,
        bold=props.bold and "bold" not in keys,
        italic=props.italic and "italic" not in keys,
        strike=props.strike and "strike" not in keys,
    )


def _flanking(before: str, after: str, *, left: bool) -> bool:
    """CommonMark's left- (``left``) or right-flanking delimiter run."""
    near, far = (_kind(after), _kind(before)) if left else (_kind(before), _kind(after))
    return near != "space" and (near != "punctuation" or far != "word")


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
            if any(not opens for *_, opens in run) and not _flanking(left, right, left=False):
                closing.update(key for _, key, opens in run if not opens)
            if any(opens for *_, opens in run) and not _flanking(left, right, left=True):
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
            wanted = _active(props[k])
            keep = 0
            while keep < len(opened) and opened[keep] in wanted:
                keep += 1
            tokens = [(_closer(key), key, False) for key in reversed(opened[keep:])]
            opened = opened[:keep]
            for key in wanted:
                if key not in opened:
                    tokens.append((_opener(key), key, True))
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
            opens = _flanking(before, after, left=True)
            closes = _flanking(before, after, left=False)
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
